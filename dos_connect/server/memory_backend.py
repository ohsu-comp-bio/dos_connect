#!/usr/bin/python
# -*- encoding: utf-8 -*-

# customize/override for your backend


import logging
import os
import uuid

from utils import AttributeDict, now, add_created_timestamps, \
                  add_updated_timestamps


log = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 100

store = AttributeDict({})


def save(doc, index='data_objects'):
    """
    save the body in the index, ensure version and id set
    """
    doc = AttributeDict(doc)
    version = doc.get('version', None)
    if not version:
        doc['version'] = now()
    if not doc.get('id', None):
        temp_id = str(uuid.uuid4())
        doc['id'] = temp_id

    if index not in store:
        store[index] = []
    doc.meta = AttributeDict({'id': doc.id})
    store[index].append(doc)
    log.info(doc.id)
    return doc


def _get(_id, current=None, index='data_objects'):
    """ get by id """
    for doc in store[index]:
        if doc.id == _id:
            if current:
                if doc.current == current:
                    return doc
            else:
                return doc


def update(_id, doc, index='data_objects'):
    """
    partial update using the contructed _id
    """
    def merge(a, b, path=None):
        "merges b into a"
        if path is None:
            path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass  # same leaf value
                else:
                    a[key] = b[key]  # update with new
            else:
                a[key] = b[key]
        return a
    store[index].append(AttributeDict(merge(_get(_id, index=index, current=True), doc)))  # noqa


def search(properties, index='data_objects', size=DEFAULT_PAGE_SIZE,
           offset=0, include_total=False):
    """
    get all objects that match
    if include_total set, return tuple (hit, total)
    """
    hits = []
    for doc in store[index]:
        if 'alias' in properties and 'aliases' in doc:
            if properties.alias in doc.aliases:
                hits.append(doc)
                continue
        if 'checksum' in properties:
            added = False
            for checksum in doc.checksums:
                if properties.checksum['checksum'] == checksum['checksum']:
                    print 'added checksum', properties.checksum['checksum']
                    hits.append(doc)
                    added = True
            if added:
                continue
        if 'url' in properties:
            added = False
            for url in doc.urls:
                if properties.url == url['url']:
                    hits.append(doc)
                    added = True
            if added:
                continue
        if 'id' in properties:
            if properties.id == doc.id and doc.current:
                hits.append(doc)
                continue
        if 'current' in properties and len(properties) == 1:
            if doc.current:
                hits.append(doc)
                continue
        if len(properties.keys()) == 0:
            hits.append(doc)
            continue

    total = len(hits)

    for _, hit in enumerate(hits):
        # for paging return the total number of matches
        if include_total:
            yield (hit, total)
        else:
            yield hit


def delete(properties, index='data_objects'):
    """
    delete item from index
    """
    indexes = []
    for i, doc in enumerate(store[index]):
        if doc.id == properties.id:
            indexes.append(i)
    for i in sorted(indexes, reverse=True):
        del store[index][i]
