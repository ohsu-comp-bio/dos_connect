"""
applications
  1. Observe buckets into registry
  2. Inventory buckets into registry
==========
This common module contains methods for logging, args, and client connection
"""
import argparse
import logging
import sys
import requests.packages.urllib3
from dos_connect.client.dos_client import Client
from bravado.requests_client import RequestsClient
import logging
import json
import os
from urlparse import urlparse
from importlib import import_module

_CLIENT = None

# import our plugin
# from file_observer_customizations import md5sum, user_metadata, before_store
customizer_name = os.getenv('CUSTOMIZER', 'dos_connect.apps.noop_customizer')
customizer = import_module(customizer_name)
_md5sum = getattr(customizer, 'md5sum')
_user_metadata = getattr(customizer, 'user_metadata')
_before_store = getattr(customizer, 'before_store')


def common_args(argparser):
    """ options common to all cli """
    argparser.add_argument('--dry_run', '-d',
                           help='dry run',
                           default=False,
                           action='store_true')
    argparser.add_argument("-v", "--verbose", help="increase output verbosity",
                           default=False,
                           action="store_true")
    return argparser


def custom_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--dos_server', '-ds',
                           help='full url of dos server',
                           default='http://localhost:8080/')

    DOS_API_KEY = os.getenv('DOS_API_KEY', None)
    argparser.add_argument('--api_key', '-api',
                           help='auth environment variable DOS_API_KEY',
                           default=DOS_API_KEY)

    DOS_USER_PASSWD = os.getenv('DOS_USER_PASSWD', None)
    argparser.add_argument('--user_pass', '-user_pass',
                           help=': delimited basic auth environment variable'
                                ' DOS_USER_PASSWD',
                           default=DOS_USER_PASSWD)


def common_logging(args):
    """ log to stdout """
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
    # https://github.com/shazow/urllib3/issues/523
    requests.packages.urllib3.disable_warnings()


def client_factory(args):
    """ create a connection """
    global _CLIENT
    if not _CLIENT:
        config = {
            'validate_requests': False,
            'validate_responses': False
        }
        http_client = RequestsClient()
        hostname = urlparse(args.dos_server).hostname
        if args.api_key:
            http_client.set_api_key(hostname, args.api_key,
                                    param_in='header')
        if args.user_pass:
            (user, passwd) = args.user_pass.split(':')
            http_client.set_basic_auth(hostname, user, passwd)

        local_client = Client(args.dos_server, config=config,
                              http_client=http_client)

        class C(object):
            def __init__(self, local_client):
                self.client = local_client.client
                self.models = local_client.models

        _CLIENT = C(local_client)

    return _CLIENT


def user_metadata(**kwargs):
    """ call plugin """
    return _user_metadata(**kwargs)


def before_store(**kwargs):
    """ call plugin """
    return _before_store(**kwargs)


def md5sum(**kwargs):
    """ call plugin """
    return _md5sum(**kwargs)


def store(args, payload):
    """ convienince method write dict to server """
    before_store(args=args, data_object=payload)
    logger = logging.getLogger(__name__)
    key = '{}~{}'.format(payload['urls'][0]['system_metadata']['event_type'],
                         payload['urls'][0]['url'])
    if not args.dry_run:
        local_client = client_factory(args)
        models = local_client.models
        client = local_client.client
        Checksum = models.get_model('ga4ghChecksum')
        URL = models.get_model('ga4ghURL')
        CreateDataObjectRequest = models.get_model(
                                    'ga4ghCreateDataObjectRequest')
        DataObject = models.get_model('ga4ghCreateDataObjectRequest')
        create_data_object = DataObject().unmarshal(payload)
        create_request = CreateDataObjectRequest(
                            data_object=create_data_object)
        create_response = client.CreateDataObject(body=create_request).result()
        data_object_id = create_response['data_object_id']
        logger.info('sent to dos_server: {} {}'.format(key, data_object_id))
    else:
        logger.info('dry_run to dos_server: {}'.format(key))
