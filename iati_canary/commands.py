from datetime import date

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
    # iatikit.download.schemas()
    # iatikit.download.data()
    pass


@click.command()
def refresh_metadata():
    '''Refresh publisher and dataset metadata.'''
    for publisher in iatikit.data().publishers:
        contact = publisher.metadata.get('publisher_contact_email', '').strip()
        if contact in ['please@update.email', 'Email not found']:
            contact = None
        pub_arr = {
            'slug': publisher.name,
            'name': publisher.metadata.get('title'),
            'contact': contact if contact else None,
        }
        try:
            pub = models.Publisher.get_by_id(publisher.name)
            [setattr(pub, k, v) for k, v in pub_arr.items()]
            pub.save()
        except DoesNotExist:
            pub = models.Publisher.create(**pub_arr)
        for dataset in publisher.datasets:
            contact = dataset.metadata.get('author_email', '').strip()
            dat_arr = {
                'slug': dataset.name,
                'name': dataset.metadata.get('title')[:255],
                'contact': contact if contact else None,
                'publisher': pub,
            }
            try:
                dat = models.Dataset.get_by_id(dataset.name)
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
        dataset = models.Dataset.get_by_id(dataset_slug)
        models.DownloadError.create(
            dataset=dataset,
            date_from=date.today(),
            error_type='download error',
        ).on_conflict_ignore().execute()


@click.command()
def xml_errors():
    '''Add XML errors to database.'''
    for d in iatikit.data().datasets:
        if d.validate_xml():
            continue
        dataset = models.Dataset.get_by_id(d.name)
        models.XMLError.create(
            dataset=dataset,
            date_from=date.today(),
            error_type='xml error',
        ).on_conflict_ignore().execute()


@click.command()
def schema_errors():
    '''Add schema errors to database.'''
    for d in iatikit.data().datasets:
        if not d.validate_xml():
            continue
        if d.validate_iati():
            continue
        dataset = models.Dataset.get_by_id(d.name)
        models.SchemaError.create(
            dataset=dataset,
            date_from=date.today(),
            error_type='schema error',
        ).on_conflict_ignore().execute()
