from datetime import datetime, timedelta

import requests

from . import models
from .extensions import db


def cleanup(days_ago):
    error_types = [
        models.DownloadError,
        models.XMLError,
        models.ValidationError,
    ]
    error_expires_at = datetime.utcnow() - timedelta(days=days_ago)
    for model in error_types:
        old_errors = model.where(currently_erroring=False,
                                 last_errored_at__lt=error_expires_at)
        for error in old_errors:
            error.delete()


def refresh_publishers():
    print('Refreshing list of publishers ...')
    url_tmpl = 'https://iatiregistry.org/api/3/action/package_search?' + \
               'start={start}&rows={page_size}'
    page = 1
    page_size = 1000
    while True:
        print(f'Page {page}')
        start = page_size * (page - 1)
        j = requests.get(url_tmpl.format(
            start=start, page_size=page_size)).json()
        if len(j['result']['results']) == 0:
            break
        for res in j['result']['results']:
            org = res['organization']
            if not org:
                continue
            org_id = org['name']
            org_name = org['title']
            pub = models.Publisher.find(org_id)
            if pub is None:
                models.Publisher.create(
                    id=org_id,
                    name=org_name,
                )
        page += 1


def refresh_metadata():
    print('Refreshing publisher and dataset metadata ...')
    error_types = [
        models.DownloadError,
        models.XMLError,
        models.ValidationError,
    ]
    url_tmpl = 'https://iatiregistry.org/api/3/action/package_search?' + \
               'q=organization:{publisher_id}&start={start}&rows={page_size}'
    page_size = 1000
    for publisher in models.Publisher.query:
        print(f'Refreshing publisher: {publisher.id}')
        page = 1
        first_pub = None
        while True:
            start = page_size * (page - 1)
            j = requests.get(url_tmpl.format(
                publisher_id=publisher.id,
                start=start,
                page_size=page_size)).json()
            for res in j['result']['results']:
                dataset_first_pub = datetime.strptime(
                    res['metadata_created'][:10],
                    '%Y-%m-%d').date()
                if not first_pub or dataset_first_pub < first_pub:
                    first_pub = dataset_first_pub
                for error_type in error_types:
                    error = error_type.where(dataset_id=res['name']).first()
                    if error:
                        error.dataset_name = res['title']
                        error.save()
            if len(j['result']['results']) < page_size:
                publisher.total_datasets = j['result']['count']
                if first_pub:
                    publisher.first_published_on = first_pub
                publisher.save()
                break
            page += 1


def fetch_errors():
    refresh_publishers()
    print('Fetching errors from github ...')
    meta = 'https://www.dropbox.com/s/6a3wggckhbb9nla/metadata.json?dl=1'
    last_errored_at = requests.get(meta).json()['started_at']
    started_at = datetime.utcnow()
    gist_base = 'https://gist.githubusercontent.com/' + \
                'andylolz/8a4e0657ec14c999de6f70f339656852/raw/'
    errors = {
        'errors': models.DownloadError,
        'xml-errors': models.XMLError,
        'validation-errors': models.ValidationError,
    }
    for slug, model in errors.items():
        print(f'Fetching {slug} ...')
        r = requests.get(gist_base + slug)
        for line in r.iter_lines():
            line = line.decode()
            if line == '.':
                break
            if slug == 'errors':
                line = line.split(' ', 1)[-1]
            line_arr = line.split(' ', 2)
            publisher_id, dataset_id, dataset_url = line_arr
            error = model.where(dataset_id=dataset_id).first()
            if error:
                if error.last_errored_at == last_errored_at:
                    continue
                error.check_count += 1
                error.error_count += 1
                error.currently_erroring = True
                error.last_errored_at = last_errored_at
                error.save()
            else:
                model.create(
                    dataset_id=dataset_id,
                    dataset_url=dataset_url,
                    publisher_id=publisher_id,
                    last_errored_at=last_errored_at,
                )
        fixed_datasets = model.where(modified_at__lt=started_at)
        for fixed_dataset in fixed_datasets:
            fixed_dataset.check_count += 1
            fixed_dataset.currently_erroring = False
            fixed_dataset.save()
    refresh_metadata()


def get_stats():
    total_publishers = models.Publisher.query.count()
    total_datasets = db.session.query(
        db.func.SUM(models.Publisher.total_datasets)
    ).first()[0]
    total_datasets = total_datasets if total_datasets else 0
    pub_errors = (models.DownloadError
                  .where(currently_erroring=True)
                  .distinct(models.DownloadError.publisher_id)
                  .all()
                  ) + \
                 (models.XMLError
                  .where(currently_erroring=True)
                  .distinct(models.XMLError.publisher_id)
                  .all()
                  )
    total_pub_errors = len(set([err.publisher_id for err in pub_errors]))
    total_download_errors = (models.DownloadError
                             .where(currently_erroring=True)
                             .count()
                             )
    total_xml_errors = (models.XMLError
                        .where(currently_erroring=True)
                        .count()
                        )
    total_dataset_errors = total_download_errors + total_xml_errors
    total_dataset_schema_errors = (models.ValidationError
                                   .where(currently_erroring=True)
                                   .count()
                                   )
    return {
        'total_publishers': total_publishers,
        'total_datasets': total_datasets,
        'total_pub_errors': total_pub_errors,
        'total_dataset_errors': total_dataset_errors,
        'total_dataset_schema_errors': total_dataset_schema_errors,
    }


def flush_emails():
    for contact in models.Contact.where(last_messaged_at=None):
        contact.send_email_confirmation()
