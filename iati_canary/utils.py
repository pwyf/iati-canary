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
    while True:
        j = requests.get(tmpl.format(
            publisher_id=publisher_id, start=start, rows=rows)).json()
        res = j['result']['results']
        if len(res) == 0:
            break
        for dataset in res:
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
            error = 'download error'
    except requests.exceptions.ConnectionError:
        error = 'download error'

    if not error:
        fresh = iatikit.Dataset(BytesIO(resp.content))
        if not fresh.validate_xml():
            error = 'xml error'
        elif not fresh.validate_iati():
            error = 'schema error'

    if not error:
        return None

    return models.DatasetError.upsert(
        dataset_id=dataset['name'],
        dataset_name=dataset['title'],
        dataset_url=url,
        publisher=pub_id,
        error_type=error,
    )
