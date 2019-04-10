from datetime import datetime
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
            validate_dataset(dataset)
        start += rows


def validate_dataset(dataset):
    print(f'Validating: {dataset["name"]}')

    pub_id = dataset.get('organization', {}).get('name')

    url = dataset['resources'][0]['url']
    error = False
    try:
        print(f'Downloading: "{url}"')
        resp = requests.get(url, verify=False,
                            headers={'User-Agent': 'IATI Canary'})
        if str(resp.status_code)[0] != '2':
            error = 'download'
    except requests.exceptions.ConnectionError:
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
