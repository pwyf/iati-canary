from peewee import CharField, DateField

from .extensions import db


class Error(db.Model):
    publisher = CharField()
    dataset = CharField()
    date = DateField()
    error = CharField()
