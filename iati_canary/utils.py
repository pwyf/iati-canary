from datetime import timedelta

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
