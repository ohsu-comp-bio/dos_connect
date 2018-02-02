#!/usr/bin/python
# -*- encoding: utf-8 -*-

# customize for your authorization needs

import flask
import logging
import os
import requests

from decorator import decorator

log = logging.getLogger(__name__)
assert os.getenv('OS_AUTH_URL', None), 'Please export openstack OS_AUTH_URL'
assert os.getenv('AUTHORIZER_PROJECTS', None), \
    'Please export openstack AUTHORIZER_PROJECTS'


# auth implementation

def _check_auth(token):
    '''This function is called to check if a token is valid.
       and user belongs to AUTHORIZER_PROJECTS'''
    # log.info('check_auth {}'.format(token))
    # validate the token
    url = '{}/auth/tokens'.format(os.environ.get('OS_AUTH_URL'))
    headers = {'X-Auth-Token': token,
               'X-Subject-Token': token}
    token_info = requests.get(url, headers=headers).json()
    if 'token' not in token_info:
        log.error(url)
        log.error(token_info)
        return False

    url = '{}/auth/projects'.format(os.environ.get('OS_AUTH_URL'))
    headers = {'X-Auth-Token': token}
    project_info = requests.get(url, headers=headers).json()
    if 'projects' not in project_info:
        log.error('no project_info for {}'.format(token))
        log.error(project_info)
        return False
    user_projects = [p['name'] for p in project_info['projects']]
    auth_projects = os.environ.get('AUTHORIZER_PROJECTS').split(',')
    auth_projects = [p.strip() for p in auth_projects]
    matched_projects = [p for p in auth_projects if p in user_projects]
    if len(matched_projects) == 0:
        log.error('no matches for {} {}'.format(user_projects, auth_projects))
        return False

    return True


def _authenticate():
    '''Sends a 401 response that enables basic auth'''
    return flask.Response('You have to provide api key', 401,
                          {'WWW-Authenticate':
                           'API key is missing or invalid'})


@decorator
def authorization_check(f, *args, **kwargs):
    '''wrap functions for authorization'''
    auth = flask.request.headers.get('Api-Key', None)
    if not auth:
        auth = flask.request.headers.get('X-API-Key', None)
    if not auth:
        log.error('authorization_check auth {}'.format(auth))
    if not auth or not _check_auth(auth):
        return _authenticate()
    return f(*args, **kwargs)
