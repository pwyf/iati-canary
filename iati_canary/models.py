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
    id = CharField(primary_key=True)
    name = CharField(max_length=1000)
    total_datasets = IntegerField(default=0)
    first_published = DateField(null=True)


class Contact(CreatedUpdatedMixin, db.Model):
    email = CharField()
    publisher = ForeignKeyField(Publisher, backref='contacts',
                                on_delete='CASCADE')
    dataset_id = CharField(null=True)

    class Meta:
        indexes = (
            (('email', 'publisher'), True),
        )


class DatasetError(CreatedUpdatedMixin, db.Model):
    dataset_id = CharField(unique=True)
    dataset_name = CharField(max_length=1000)
    dataset_url = CharField()
    publisher = ForeignKeyField(Publisher, backref='errors',
                                on_delete='CASCADE')
    error_type = CharField()
    error_count = IntegerField(default=1)
    last_seen_at = DateTimeField(default=datetime.now)
