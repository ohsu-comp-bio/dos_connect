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
from ga4gh.dos.client import Client
from bravado.requests_client import RequestsClient
import logging
import json
import os
from urlparse import urlparse
from importlib import import_module

_CLIENT = None

# import our plugin
customizer_name = os.getenv('CUSTOMIZER', 'dos_connect.apps.noop_customizer')
customizer = import_module(customizer_name)
_md5sum = getattr(customizer, 'md5sum')
_user_metadata = getattr(customizer, 'user_metadata')
_before_store = getattr(customizer, 'before_store')
_id = getattr(customizer, 'id')


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
    argparser.add_argument('--user_pass', '-up',
                           help=': delimited basic auth environment variable'
                                ' DOS_USER_PASSWD',
                           default=DOS_USER_PASSWD)

    argparser.add_argument('--api_key_name', '-kn',
                           help='api key name',
                           default='X-API-Key')


def common_logging(args):
    """ log to stdout """
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
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
                                    param_name=args.api_key_name,
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


def id(**kwargs):
    """ call plugin """
    return _id(**kwargs)


def store(args, payload):
    """ convienince method write dict to server """
    before_store(args=args, data_object_dict=payload)
    logger = logging.getLogger(__name__)
    event_type = payload['urls'][0]['system_metadata']['event_type']
    key = '{}~{}'.format(event_type,
                         payload['urls'][0]['url'])

    object_action = event_type.split(':')[0]
    # 'Microsoft.Storage.BlobDeleted': 'ObjectRemoved:Delete',
    # 'OBJECT_ARCHIVE': 'ObjectCreated:Copy',
    # 'Microsoft.Storage.BlobCreated': 'ObjectCreated:Put',
    # 'OBJECT_METADATA_UPDATE': 'ObjectModified'

    if not args.dry_run:
        local_client = client_factory(args)
        models = local_client.models
        client = local_client.client
        CreateDataObjectRequest = models.get_model(
                                    'CreateDataObjectRequest')
        DataObject = models.get_model('DataObject')
        data_object = DataObject().unmarshal(payload)
        create_request = CreateDataObjectRequest(data_object=data_object)
        data_object = create_request.data_object
        # call plugin
        constructed_id = id(data_object=data_object)
        if constructed_id:
            data_object.id = constructed_id
            logger.info('set id to {}'.format(data_object.id))
        else:
            logger.info('data_object id was {}'.format(data_object.id))
        create_request = CreateDataObjectRequest(data_object=data_object)
        create_response = client.CreateDataObject(body=create_request).result()
        data_object_id = create_response['data_object_id']
        logger.info('sent to dos_server: {} {}'.format(key, data_object_id))
    else:
        logger.info('dry_run to dos_server: {}'.format(key))
