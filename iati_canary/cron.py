import iatikit
import requests


iatikit.download.schemas()
iatikit.download.data()

datasets = iatikit.data().datasets
[d.name for d in datasets if not d.validate_xml()]

gist_url = 'https://gist.githubusercontent.com/andylolz/' + \
           '8a4e0657ec14c999de6f70f339656852/raw/errors'
r = requests.get(gist_url)
for line in r.iter_lines():
    if line == b'.':
        break
    status_code, publisher, dataset, url = line.split(b' ')
