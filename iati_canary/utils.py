from datetime import datetime, timedelta

import requests

from . import models


def cleanup(days_ago):
    errors = models.DatasetError.with_subquery('publisher')
    for error in errors:
        ref_datetime = error.publisher.last_checked_at - \
                       timedelta(days=days_ago)
        if error.last_errored_at < ref_datetime:
            error.delete()


def refresh_metadata():
    started_at = datetime.utcnow()
    error_types = [
        models.DownloadError,
        models.XMLError,
        models.ValidationError,
    ]
    url_tmpl = 'https://iatiregistry.org/api/3/action/package_search' + \
               '?start={start}&rows={page_size}'
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
            first_pub = datetime.strptime(
                res['metadata_created'][:10], '%Y-%m-%d').date()
            pub = models.Publisher.find(org_id)
            if pub is None:
                models.Publisher.create(
                    id=org_id,
                    name=org_name,
                    total_datasets=1,
                    first_published_on=first_pub,
                )
            else:
                if pub.created_at > started_at:
                    pub.total_datasets += 1
                    if first_pub < pub.first_published_on:
                        pub.first_published_on = first_pub
                    pub.save()

            for error_type in error_types:
                error = error_type.where(dataset_id=res['name']).first()
                if error:
                    error.dataset_name = res['title']
                    error.save()
        page += 1


def fetch_errors():
    refresh_metadata()
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
