#!/usr/bin/python
# -*- encoding: utf-8 -*-

import datetime
import json


class AttributeDict(dict):
    """
    use dot notation for dicts
    """
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def to_dict(self):
        return json.loads(json.dumps(self))


def now():
    """
    get string iso date in zulu
    """
    return str(datetime.datetime.now().isoformat("T") + "Z")


def add_created_timestamps(doc):
    """
    Adds created and updated timestamps to the document.
    """
    if 'created' not in doc:
        doc['created'] = now()
    if 'updated' not in doc:
        doc['updated'] = now()
    return doc


def add_updated_timestamps(doc):
    """
    Adds updated timestamp to the document.
    """
    if 'updated' not in doc:
        doc['updated'] = now()
    return doc
