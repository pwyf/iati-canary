from io import BytesIO

import requests
import iatikit

from . import models


def validate_dataset(dataset_id):
    dataset = iatikit.data().datasets.get(dataset_id)

    pub_id = dataset.metadata.get('organization', {}).get('name')
    publisher = models.Publisher.get_by_id(pub_id)

    url = dataset.metadata['resources'][0]['url']
    error = False
    try:
        resp = requests.get(url, verify=False)
        if str(resp.status_code)[0] != '2':
            error = 'download error'
    except requests.exceptions.ConnectionError:
        error = 'download error'

    if not error:
        dataset = iatikit.Dataset(BytesIO(resp.content),
                                  dataset.metadata_path)
        if not dataset.validate_xml():
            error = 'xml error'
        elif not dataset.validate_iati():
            error = 'schema error'

    if not error:
        return None

    return models.DatasetError.upsert(
        dataset_id=dataset.name,
        dataset_name=dataset.metadata.get('title'),
        dataset_url=dataset.metadata['resources'][0]['url'],
        publisher=publisher,
        error_type=error,
    )
