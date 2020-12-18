#!/usr/bin/env python

import requests
import datetime
from xml.etree import ElementTree
import io
import logging
import argparse

parser = argparse.ArgumentParser(description='Create bibliography from inspirehep',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='example: create_bibtex.py --query author%3AR.Turra.1%20and%20collection%3APublished where R.Turra.1 is from here: https://inspirehep.net/authors?sort=bestmatch&size=25&page=1&q=turra')
parser.add_argument('--baseurl', default="https://inspirehep.net/api/")
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
    query = 'literature?'
    query += '&'.join([k + "=" + str(v) for k, v in list(kwargs.items())])
    return query


def build_all_queries(nper_step=50, **kwargs):
    kwargs['size'] = nper_step
    kwargs['page'] = 1
    while True:
        yield build_query(**kwargs)
        kwargs['page'] += 1


inspire_args = {'q': args.query, 'format': 'bibtex',
                #'of': 'hx', 'em': 'B', 'sf': 'year', 'so': 'd', 'rg': 5, 'tc': 'p'
                }

bibtex = ""

for query in build_all_queries(**inspire_args):
    url = BASEURL + query
    r = requests.get(url)
    if not r.status_code == requests.codes.ok:
        raise IOError("cannot connect to %s, code: %s" % (url, r.status_code))

    content = r.text  # this is unicode

    if content.count('@') == 0:
        break

    try:
        bibtex += content
    except AttributeError:
        # special case for python < 2.7
        def itertext(self):
            tag = self.tag
            if not isinstance(tag, str) and tag is not None:
                return
            if self.text:
                yield self.text
            for e in self:
                for s in itertext(e):
                    yield s
                if e.tail:
                    yield e.tail
        bibtex += ''.join(itertext(ElementTree.fromstring(r.content)))
    bibtex += r"%% ==============="
    logger.info('%d items found...', bibtex.count('@'))

logger.info('%d items found', bibtex.count('@'))
with io.open('bibtex_%s.bib' % str(datetime.date.today()), 'w') as f:
    f.write(bibtex)
