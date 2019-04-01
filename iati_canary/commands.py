from os.path import join
import json
from datetime import datetime, timedelta

import iatikit
import click
from peewee import DoesNotExist

from .extensions import db
from .utils import validate_publisher_datasets
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
def refresh_schemas():
    '''Refresh IATI schemas.'''
    iatikit.download.schemas()


@click.command()
def refresh_metadata():
    '''Refresh publisher metadata.'''
    iatikit.download.metadata()
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(join('__iatikitcache__', 'registry', 'metadata.json'), 'w') as f:
        json.dump({'updated_at': now}, f)

    for publisher in iatikit.data().publishers:
        # contacts = {}
        # contact = publisher.metadata.get('publisher_contact_email', '').strip()
        # if contact in ['please@update.email', 'Email not found', '']:
        #     contact = None
        # if contact:
        #     contacts[contact] = None
        first_pub = datetime.strptime(
            min([d.metadata.get('metadata_created')
                 for d in publisher.datasets]), '%Y-%m-%dT%H:%M:%S.%f').date()
        pub_arr = {
            'id': publisher.name,
            'name': publisher.metadata.get('title'),
            'total_datasets': len(publisher.datasets),
            'first_published_on': first_pub,
        }
        try:
            pub = models.Publisher.get_by_id(publisher.name)
            [setattr(pub, k, v) for k, v in pub_arr.items()]
            pub.save()
        except DoesNotExist:
            pub = models.Publisher.create(**pub_arr)
        # for dataset in publisher.datasets:
        #     contact = dataset.metadata.get('author_email', '').strip()
        #     if contact not in contacts:
        #         contacts[contact] = dataset.name
        # for contact, dataset_id in contacts.items():
        #     con_arr = {
        #         'email': contact,
        #         'publisher': pub,
        #         'dataset_id': dataset_id,
        #     }
        #     try:
        #         models.Contact.create(**con_arr)
        #     except:
        #         db.database.rollback()


@click.command()
@click.option('--count', type=int, default=1)
def validate(count):
    '''Validate datasets, and add errors to database.'''
    publishers = models.Publisher.select().order_by(
        models.Publisher.queued_at.asc())
    for idx, publisher in enumerate(publishers):
        if idx >= count:
            break
        publisher.last_checked_at = datetime.now()
        validate_publisher_datasets(publisher.id)
        publisher.queued_at = datetime.now()
        publisher.save()


@click.command()
@click.option('--days-ago', type=int, default=5)
def cleanup(days_ago):
    '''Clean expired errors from the database.'''
    errors = (models.DatasetError
              .select(models.DatasetError, models.Publisher)
              .join(models.Publisher))
    for error in errors:
        ref_datetime = error.publisher.last_checked_at - timedelta(days=5)
        if error.last_errored_at < ref_datetime:
            error.delete_instance()
