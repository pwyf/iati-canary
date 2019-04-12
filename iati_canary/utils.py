from datetime import timedelta
from io import BytesIO

import requests
import iatikit

from . import models


def validate_publisher_datasets(publisher_id):
    # first, download metadata for publisher datasets
    start = 0
    rows = 50
    tmpl = 'https://iatiregistry.org/api/3/action/package_search?' + \
           'q=organization:{publisher_id}&start={start}&rows={rows}'
    first_pub = None
    while True:
        j = requests.get(tmpl.format(
            publisher_id=publisher_id, start=start, rows=rows)).json()
        res = j['result']['results']
        if len(res) == 0:
            pub = models.Publisher.find(publisher_id)
            pub.total_datasets = j['result']['count']
            pub.first_published_on = first_pub
            pub.save()
            break
        for dataset in res:
            published = dataset['metadata_created'][:10]
            if first_pub is None or published < first_pub:
                first_pub = published
            validate_dataset(dataset, ignore_after=pub.last_checked_at)
        start += rows


def validate_dataset(dataset, ignore_after=None):
    print(f'Validating: {dataset["name"]}')

    pub_id = dataset.get('organization', {}).get('name')

    d = models.DatasetError.where(dataset_id=dataset['name'])
    if ignore_after and d.last_errored_at > ignore_after:
        return

    url = dataset['resources'][0]['url']
    error = False
    try:
        print(f'Downloading: "{url}"')
        resp = requests.get(url, verify=False, timeout=30,
                            headers={'User-Agent': 'IATI Canary'})
        if str(resp.status_code)[0] != '2':
            error = 'download'
    except requests.exceptions.ConnectionError:
        error = 'download'
    except requests.exceptions.Timeout:
        error = 'download'

    if not error:
        fresh = iatikit.Dataset(BytesIO(resp.content))
        if not fresh.validate_xml():
            error = 'xml'
        elif not fresh.validate_iati():
            error = 'schema'

    models.DatasetError.upsert(
        success=not error,
        dataset_id=dataset['name'],
        dataset_name=dataset['title'],
        dataset_url=url,
        publisher_id=pub_id,
        error_type=error,
    )


def cleanup(days_ago):
    errors = models.DatasetError.with_subquery('publisher')
    for error in errors:
        ref_datetime = error.publisher.last_checked_at - \
                       timedelta(days=days_ago)
        if error.last_errored_at < ref_datetime:
            error.delete()


def refresh_schemas():
    '''Refresh IATI schemas.'''
    iatikit.download.schemas()


def refresh_metadata():
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
            if models.Publisher.find(org_id) is None:
                models.Publisher.create(id=org_id, name=org_name)
        page += 1
