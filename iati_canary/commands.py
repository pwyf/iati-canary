from os.path import join
import json
from datetime import datetime, timedelta

from flask.cli import with_appcontext
import iatikit
import click
from sqlalchemy_mixins import ModelNotFoundError

from .utils import validate_publisher_datasets
from . import models


@click.command()
def refresh_schemas():
    '''Refresh IATI schemas.'''
    iatikit.download.schemas()


@click.command()
@with_appcontext
def refresh_metadata():
    '''Refresh publisher metadata.'''
    iatikit.download.metadata()
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(join('__iatikitcache__', 'registry', 'metadata.json'), 'w') as f:
        json.dump({'updated_at': now}, f)

    for publisher in iatikit.data().publishers:
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
            pub = models.Publisher.find_or_fail(publisher.name)
            [setattr(pub, k, v) for k, v in pub_arr.items()]
            pub.save()
        except ModelNotFoundError:
            pub = models.Publisher.create(**pub_arr)


@click.command()
@click.option('--count', type=int, default=None)
@with_appcontext
def validate(count):
    '''Validate datasets, and add errors to database.'''
    idx = 0
    while True:
        if count and idx >= count:
            break
        publisher = models.Publisher.sort('queued_at').first()
        publisher.last_checked_at = datetime.now()
        validate_publisher_datasets(publisher.id)
        publisher.queued_at = datetime.now()
        publisher.save()
        idx += 1


@click.command()
@click.option('--days-ago', type=int, default=5)
@with_appcontext
def cleanup(days_ago):
    '''Clean expired errors from the database.'''
    errors = models.DatasetError.with_subquery('publisher')
    for error in errors:
        ref_datetime = error.publisher.last_checked_at - \
                       timedelta(days=days_ago)
        if error.last_errored_at < ref_datetime:
            error.delete()
