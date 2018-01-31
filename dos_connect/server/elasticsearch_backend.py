#!/usr/bin/python
# -*- encoding: utf-8 -*-

# customize/override for your backend


import logging
import os
import uuid


from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from utils import AttributeDict, now, add_created_timestamps, \
                  add_updated_timestamps


log = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 100

# connect to elastic

ELASTIC_URL = os.getenv('ELASTIC_URL', 'localhost:9200')
client = Elasticsearch([ELASTIC_URL])
assert client.info()
# check persistence options in env
ES_REFRESH_ON_PERSIST = os.getenv('ES_REFRESH_ON_PERSIST', 'False')
ES_REFRESH_ON_PERSIST = not (ES_REFRESH_ON_PERSIST == 'False')
if not ES_REFRESH_ON_PERSIST:
    log.info('ES_REFRESH_ON_PERSIST not set (default),'
             ' ES writes defer index refresh')
else:
    log.info('ES_REFRESH_ON_PERSIST set, ES writes will refresh index')


def save(doc, index='data_objects'):
    """
    save the body in the index, ensure version and id set
    """
    version = doc.get('version', None)
    if not version:
        doc['version'] = now()
    if not doc.get('id', None):
        temp_id = str(uuid.uuid4())
        doc['id'] = temp_id
    # create index, use index name singular as doc type
    # do not wait for search available See
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-refresh.html
    result = client.index(index=index,
                          body=doc,
                          doc_type=index[:-1],
                          timeout='120s',
                          request_timeout=120,
                          op_type='index',
                          refresh=ES_REFRESH_ON_PERSIST
                          )
    return doc


def update(_id, doc, index='data_objects'):
    """
    partial update using the es contructed _id
    """
    log.debug(doc)
    result = client.update(index=index,
                           doc_type=index[:-1],
                           id=_id,
                           body={"doc": doc},
                           refresh=ES_REFRESH_ON_PERSIST
                           )
    log.debug(result)


def search(properties, index='data_objects', size=DEFAULT_PAGE_SIZE,
           offset=0, include_total=False):
    """
    get all objects that match
    if include_total set, return tuple (hit, total)
    """
    #  see https://github.com/ga4gh/data-object-schemas/issues/33
    # make seach parameters ES friendly
    if 'alias' in properties:
        properties.aliases = properties.alias
        del properties['alias']
    if 'checksum' in properties:
        properties['checksums.checksum'] = properties.checksum['checksum']
        del properties['checksum']
    if 'url' in properties:
        properties['urls.url'] = properties.url
        del properties['url']
    # by default search for everything
    s = Search(using=client, index=index)
    clauses = ['*']
    for k in properties.keys():
        v = properties[k]
        # quote everything except booleans
        if not isinstance(v, bool):
            clauses.append('+{}:"{}"'.format(k, v))
        else:
            clauses.append('+{}:{}'.format(k, str(v).lower()))
    s = s.query("query_string", query=' '.join(clauses))
    # get current page
    s = s[offset:offset+size]
    # sorted by updated desc
    s = s.sort('-updated')
    response = s.execute()
    total = response.hits.total
    for _, hit in enumerate(response):
        # for paging return the total number of matches
        if include_total:
            yield (hit, total)
        else:
            yield hit


def delete(properties, index='data_objects'):
    """
    delete item from index
    """
    s = Search(using=client, index=index)
    clauses = []
    for k in properties.keys():
        v = properties[k]
        clauses.append('+{}:"{}"'.format(k, v))
    s = s.query("query_string", query=' '.join(clauses))
    s.delete()
