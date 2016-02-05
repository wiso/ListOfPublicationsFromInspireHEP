import requests
from xml.etree import ElementTree
import io


BASEURL = "https://inspirehep.net/"


def build_query(**kwargs):
    query = 'search?'
    query += '&'.join([k + "=" + str(v) for k, v in kwargs.iteritems()])
    return query


def build_all_queries(nper_step=50, **kwargs):
    kwargs['rg'] = nper_step
    if 'jrec' not in kwargs:
        kwargs['jrec'] = 1
    while True:
        yield build_query(**kwargs)
        kwargs['jrec'] += nper_step


args = {'p': 'author%3AR.Turra.1+AND+collection%3Apublished',
        'of': 'hx', 'em': 'B', 'sf': 'year', 'so': 'd', 'rg': 5, 'tc': 'p', 'jrec': 1}

bibtex = u""

for query in build_all_queries(**args):
    url = BASEURL + query
    r = requests.get(url)
    if not r.status_code == requests.codes.ok:
        raise IOError("cannot connect to %s" % url)

    content = r.content

    if content.count('@') == 0:
        break

    bibtex += ''.join(ElementTree.fromstring(r.content).itertext())
    bibtex += r"%% ==============="
    print '%d items found' % bibtex.count('@')

print '%d items found' % bibtex.count('@')
f = io.open('bibtex.bib', 'w')
f.write(bibtex)
