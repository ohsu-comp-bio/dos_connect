from ga4gh.dos.client import Client
import logging
import json
from .. import common_args, common_logging

_CLIENT = None


def store(args, payload):
    logger = logging.getLogger(__name__)
    """ write dict to kafka """
    key = '{}~{}'.format(payload['urls'][0]['system_metadata']['event_type'],
                         payload['urls'][0]['url'])
    if not args.dry_run:
        server = _server(args)
        models = server['models']
        client = server['client']
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


def custom_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--dos_server', '-ds',
                           help='full url of dos server',
                           default='http://localhost:8080/')


def _server(args):
    """ create a connection """
    global _CLIENT
    if not _CLIENT:
        config = {
            'validate_requests': False,
            'validate_responses': False
        }
        local_client = Client(args.dos_server, config=config)
        _CLIENT = {
            'client': local_client.client,
            'models': local_client.models
        }
    return _CLIENT
