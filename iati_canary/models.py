from datetime import datetime

from peewee import CharField, DateTimeField, ForeignKeyField

from .extensions import db


class CreatedUpdatedMixin(db.Model):
    created_at = DateTimeField(default=datetime.now)
    modified_at = DateTimeField()

    def save(self, *args, **kwargs):
        self.modified_at = datetime.now()
        return super(CreatedUpdatedMixin, self).save(*args, **kwargs)


class Publisher(CreatedUpdatedMixin, db.Model):
    slug = CharField(primary_key=True)
    name = CharField(max_length=1000)
    contact = CharField(null=True)


class Dataset(CreatedUpdatedMixin, db.Model):
    slug = CharField(primary_key=True)
    name = CharField(max_length=1000)
    contact = CharField(null=True)
    publisher = ForeignKeyField(Publisher, backref='datasets')


class DatasetError(CreatedUpdatedMixin, db.Model):
    dataset = ForeignKeyField(Dataset, backref='errors')
    error_type = CharField()

    class Meta:
        indexes = (
            (('dataset', 'date_from'), True),
        )
