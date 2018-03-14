"""
dos_connect
==========
Provides
  1. Observe buckets into registry
  2. Inventory buckets into registry
  3. Web app to query into registry
"""

import logging
from bravado.requests_client import RequestsClient
from dos_connect.client.dos_client import Client
SERVER_URL = 'http://localhost:8080/ga4gh/dos/v1'


def init_logging():
    """ setup logging """
    root = logging.getLogger()
    root.setLevel(logging.ERROR)
    logging.captureWarnings(True)


def init_client():
    """ setup client """
    http_client = RequestsClient()
    # http_client.set_basic_auth('localhost', 'admin', 'secret')
    # http_client.set_api_key('localhost', 'XXX-YYY-ZZZ', param_in='header')
    return Client(SERVER_URL, http_client=http_client)
