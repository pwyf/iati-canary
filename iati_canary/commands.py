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
def download_errors():
    '''Add download errors to database.'''
    data = iatikit.data()
    gist_url = 'https://gist.githubusercontent.com/andylolz/' + \
               '8a4e0657ec14c999de6f70f339656852/raw/errors'
    r = requests.get(gist_url)
    for line in r.iter_lines():
        line = line.decode()
        if line == '.':
            break
        status_code, publisher_id, dataset_id, url = line.split(' ')

        try:
            resp = requests.get(url, verify=False)
            if str(resp.status_code)[0] == '2':
                continue
        except:
            pass

        dataset = data.datasets.get(dataset_id)
        publisher = models.Publisher.get_by_id(publisher_id)

        error = models.DatasetError.get_or_none(dataset_id=dataset_id)
        if error and error.error_type != 'download error':
            error.delete().execute()
            error = None
        if error:
            error.last_seen_at = datetime.now()
            error.error_count += 1
            error.save()
        else:
            models.DatasetError(
                dataset_id=dataset_id,
                dataset_name=dataset.metadata.get('title'),
                dataset_url=url,
                publisher=publisher,
                error_type='download error',
            ).save()


@click.command()
def xml_errors():
    '''Add XML errors to database.'''
    for p in iatikit.data().publishers:
        publisher = None
        for dataset in p.datasets:
            if dataset.validate_xml():
                continue
            if not publisher:
                publisher = models.Publisher.get_by_id(p.name)
            error = models.DatasetError.get_or_none(dataset_id=dataset.name)
            if error:
                if error.error_type == 'download error':
                    continue
                elif error.error_type == 'schema error':
                    error.delete().execute()
                    error = None
            if error:
                error.last_seen_at = datetime.now()
                error.error_count += 1
                error.save()
            else:
                models.DatasetError(
                    dataset_id=dataset.name,
                    dataset_name=dataset.metadata.get('title'),
                    dataset_url=dataset.metadata['resources'][0]['url'],
                    publisher=publisher,
                    error_type='xml error',
                ).save()


@click.command()
def schema_errors():
    '''Add schema errors to database.'''
    for p in iatikit.data().publishers:
        publisher = None
        for dataset in p.datasets:
            if not dataset.validate_xml():
                continue
            if dataset.validate_iati():
                continue
            if not publisher:
                publisher = models.Publisher.get_by_id(p.name)
            error = models.DatasetError.get_or_none(dataset_id=dataset.name)
            if error and error.error_type != 'schema error':
                continue
            if error:
                error.last_seen_at = datetime.now()
                error.error_count += 1
                error.save()
            else:
                models.DatasetError(
                    dataset_id=dataset.name,
                    dataset_name=dataset.metadata.get('title'),
                    dataset_url=dataset.metadata['resources'][0]['url'],
                    publisher=publisher,
                    error_type='schema error',
                ).save()
