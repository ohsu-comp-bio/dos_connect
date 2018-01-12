#!/usr/bin/python
# -*- encoding: utf-8 -*-

# customize for your authorization needs

import flask
import logging
from decorator import decorator

log = logging.getLogger(__name__)


# auth implementation

def check_auth(username, password):
    '''This function is called to check if a username /
    password combination is valid.'''
    log.info('check_auth {} {}'.format(username, password))
    return username == 'admin' and password == 'secret'


def authenticate():
    '''Sends a 401 response that enables basic auth'''
    return flask.Response('You have to login with proper credentials', 401,
                          {'WWW-Authenticate': 'Basic realm="Login Required"'})


@decorator
def authorization_check(f, *args, **kwargs):
    auth = flask.request.authorization
    log.info('authorization_check {}'.format(auth))
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return f(*args, **kwargs)
