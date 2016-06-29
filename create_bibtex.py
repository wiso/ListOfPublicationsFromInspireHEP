#!/usr/bin/env python

import requests
import datetime
from xml.etree import ElementTree
import io
import logging
import argparse

parser = argparse.ArgumentParser(description='Create bibliography from inspirehep',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='example: create_bibtex.py --query author%3AR.Turra.1+AND+collection%3Apublished where R.Turra.1 is from here: https://inspirehep.net/author/profile/R.Turra.1')
parser.add_argument('--baseurl', default="https://inspirehep.net/")
parser.add_argument('--query', help='query', required=True)
args = parser.parse_args()

logger = logging.getLogger('create bibtex')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
BASEURL = args.baseurl


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


inspire_args = {'p': args.query,
                'of': 'hx', 'em': 'B', 'sf': 'year', 'so': 'd', 'rg': 5, 'tc': 'p', 'jrec': 1}

bibtex = u""

for query in build_all_queries(**inspire_args):
    url = BASEURL + query
    r = requests.get(url)
    if not r.status_code == requests.codes.ok:
        raise IOError("cannot connect to %s" % url)

    content = r.content

    if content.count('@') == 0:
        break

    bibtex += ''.join(ElementTree.fromstring(r.content).itertext())
    bibtex += r"%% ==============="
    logger.info('%d items found...', bibtex.count('@'))

logger.info('%d items found', bibtex.count('@'))
with io.open('bibtex_%s.bib' % str(datetime.date.today()), 'w') as f:
    f.write(bibtex)
