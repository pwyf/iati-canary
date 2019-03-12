import os
from datetime import datetime

import iatikit
import click
from peewee import DoesNotExist

from .extensions import db
from .utils import validate_dataset
from . import models


@click.command()
def init_db():
    '''Initialise the database.'''
    db.database.create_tables([
        models.Publisher,
        models.Contact,
        models.DatasetError,
    ])


@click.command()
def refresh_iati():
    '''Refresh IATI data and schemas.'''
    iatikit.download.schemas()
    iatikit.download.data()


@click.command()
def refresh_metadata():
    '''Refresh publisher and dataset metadata.'''
    for publisher in iatikit.data().publishers:
        contacts = []
        contact = publisher.metadata.get('publisher_contact_email', '').strip()
        if contact in ['please@update.email', 'Email not found', '']:
            contact = None
        if contact:
            contacts.append((contact, None))
        first_pub = datetime.strptime(
            min([d.metadata.get('metadata_created')
                 for d in publisher.datasets]), '%Y-%m-%dT%H:%M:%S.%f').date()
        pub_arr = {
            'id': publisher.name,
            'name': publisher.metadata.get('title'),
            'total_datasets': len(publisher.datasets),
            'first_published': first_pub,
        }
        try:
            pub = models.Publisher.get_by_id(publisher.name)
            [setattr(pub, k, v) for k, v in pub_arr.items()]
            pub.save()
        except DoesNotExist:
            pub = models.Publisher.create(**pub_arr)
        for dataset in publisher.datasets:
            contact = dataset.metadata.get('author_email', '').strip()
            if contact:
                contacts.append((contact, dataset.name))
        for contact, dataset_id in set(contacts):
            con_arr = {
                'email': contact,
                'publisher': pub,
                'dataset_id': dataset_id,
            }
            try:
                models.Contact.create(**con_arr)
            except:
                db.database.rollback()


@click.command()
def validate():
    '''Validate datasets, and add errors to database.'''
    for dataset in iatikit.data().datasets:
        if not dataset.validate_xml() or not dataset.validate_iati():
            validate_dataset(dataset.name)

        os.remove(dataset.data_path)
        os.remove(dataset.metadata_path)
