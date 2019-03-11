from datetime import datetime

from peewee import (CharField, DateField, DateTimeField,
                    ForeignKeyField, IntegerField)

from .extensions import db


class CreatedUpdatedMixin(db.Model):
    created_at = DateTimeField(default=datetime.now)
    modified_at = DateTimeField()

    def save(self, *args, **kwargs):
        self.modified_at = datetime.now()
        return super(CreatedUpdatedMixin, self).save(*args, **kwargs)


class Publisher(CreatedUpdatedMixin, db.Model):
    slug = CharField(index=True)
    name = CharField(max_length=1000)
    contact = CharField(null=True)
    total_datasets = IntegerField(default=0)
    first_published = DateField(null=True)


class Dataset(CreatedUpdatedMixin, db.Model):
    slug = CharField(index=True)
    name = CharField(max_length=1000)
    url = CharField(max_length=1000)
    contact = CharField(null=True)
    publisher = ForeignKeyField(Publisher, backref='datasets')


class DatasetError(CreatedUpdatedMixin, db.Model):
    dataset = ForeignKeyField(Dataset, backref='errors', unique=True)
    error_type = CharField()
