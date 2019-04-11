from datetime import datetime

from flask.cli import with_appcontext
import click

from . import models, utils


@click.command()
def refresh_schemas():
    '''Refresh IATI schemas.'''
    utils.refresh_schemas()


@click.command()
@with_appcontext
def refresh_metadata():
    '''Refresh publisher metadata.'''
    utils.refresh_metadata()


@click.command()
@click.option('--count', type=int, default=None)
@with_appcontext
def validate(count):
    '''Validate datasets, and add errors to database.'''
    idx = 0
    while True:
        if count is None and idx % 100 == 0:
            # do a refresh every 100 orgs
            utils.refresh_metadata()
            utils.refresh_schemas()
            utils.cleanup(5)
        if count and idx >= count:
            break
        publisher = models.Publisher.sort('queued_at').first()
        publisher.last_checked_at = datetime.now()
        utils.validate_publisher_datasets(publisher.id)
        publisher.queued_at = datetime.now()
        publisher.save()
        idx += 1


@click.command()
@click.option('--days-ago', type=int, default=5)
@with_appcontext
def cleanup(days_ago):
    '''Clean expired errors from the database.'''
    utils.cleanup(days_ago)
