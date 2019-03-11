from datetime import datetime

import iatikit
import requests
import click
from peewee import DoesNotExist

from .extensions import db
from . import models


@click.command()
def init_db():
    '''Initialise the database.'''
    db.database.create_tables([
        models.Publisher,
        models.Dataset,
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
        contact = publisher.metadata.get('publisher_contact_email', '').strip()
        if contact in ['please@update.email', 'Email not found']:
            contact = None
        first_pub = datetime.strptime(
            min([d.metadata.get('metadata_created')
                 for d in publisher.datasets]), '%Y-%m-%dT%H:%M:%S.%f').date()
        pub_arr = {
            'slug': publisher.name,
            'name': publisher.metadata.get('title'),
            'contact': contact if contact else None,
            'total_datasets': len(publisher.datasets),
            'first_published': first_pub,
        }
        try:
            pub = models.Publisher.get(slug=publisher.name)
            [setattr(pub, k, v) for k, v in pub_arr.items()]
            pub.save()
        except DoesNotExist:
            pub = models.Publisher.create(**pub_arr)
        for dataset in publisher.datasets:
            contact = dataset.metadata.get('author_email', '').strip()
            dat_arr = {
                'slug': dataset.name,
                'name': dataset.metadata.get('title'),
                'url': dataset.metadata['resources'][0]['url'],
                'contact': contact if contact else None,
                'publisher': pub,
            }
            try:
                dat = models.Dataset.get(slug=dataset.name)
                [setattr(dat, k, v) for k, v in dat_arr.items()]
                dat.save()
            except DoesNotExist:
                models.Dataset.create(**dat_arr)


@click.command()
def download_errors():
    '''Add download errors to database.'''
    gist_url = 'https://gist.githubusercontent.com/andylolz/' + \
               '8a4e0657ec14c999de6f70f339656852/raw/errors'
    r = requests.get(gist_url)
    for line in r.iter_lines():
        if line == b'.':
            break
        status_code, _, dataset_slug, url = line.split(b' ')
        dataset = models.Dataset.get(slug=dataset_slug)
        try:
            models.DatasetError(
                dataset=dataset,
                error_type='download error',
            ).save()
        except:
            db.database.rollback()


@click.command()
def xml_errors():
    '''Add XML errors to database.'''
    for d in iatikit.data().datasets:
        if d.validate_xml():
            continue
        dataset = models.Dataset.get(slug=d.name)
        try:
            models.DatasetError(
                dataset=dataset,
                error_type='xml error',
            ).save()
        except:
            db.database.rollback()


@click.command()
def schema_errors():
    '''Add schema errors to database.'''
    for d in iatikit.data().datasets:
        if not d.validate_xml():
            continue
        if d.validate_iati():
            continue
        dataset = models.Dataset.get(slug=d.name)
        try:
            models.DatasetError(
                dataset=dataset,
                error_type='schema error',
            ).save()
        except:
            db.database.rollback()
