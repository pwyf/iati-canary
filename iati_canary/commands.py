from os.path import join
import json
from datetime import datetime, timedelta

from flask.cli import with_appcontext
import iatikit
import requests
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
    url_tmpl = 'https://iatiregistry.org/api/3/action/package_search' + \
               '?start={start}&rows=1000'
    org_url_tmpl = 'https://iatiregistry.org/api/3/action/group_show' + \
                   '?id={org_slug}'
    page = 1
    page_size = 1000
    while True:
        print(f'Page {page}')
        start = page_size * (page - 1)
        j = requests.get(url_tmpl.format(start=start)).json()
        if len(j['result']['results']) == 0:
            break
        for res in j['result']['results']:
            org = res['organization']
            if not org:
                continue
            org_id = org['name']
            org_name = org['title']
            if models.Publisher.find(org_id) is None:
                models.Publisher.create(id=org_id, name=org_name)
        page += 1


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
