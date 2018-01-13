#!/usr/bin/python
# -*- encoding: utf-8 -*-

# customize for your authorization needs

import flask
import logging
from decorator import decorator

log = logging.getLogger(__name__)


# auth implementation

@decorator
def authorization_check(f, *args, **kwargs):
    '''wrap functions for authorization always OK'''
    auth = flask.request.headers['Api-Key']
    log.info('authorization_check auth {}'.format(auth))
    return f(*args, **kwargs)
