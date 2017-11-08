from azure.storage.blob import BlockBlobService
from azure.common import AzureException
# https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blob-event-overview
# https://docs.microsoft.com/en-us/azure/storage/queues/storage-python-how-to-use-queue-storage
# https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blob-event-quickstart

import json
import argparse
import logging
import urllib
import time
import pprint
import os
from urlparse import urlparse
import sys
import datetime
import attr

from customizations import store, custom_args


logger = logging.getLogger('azure-inventory')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


# Instantiates a storage client
block_blob_service = BlockBlobService(
                        account_name=os.environ.get('BLOB_STORAGE_ACCOUNT'),
                        account_key=os.environ.get('BLOB_STORAGE_ACCESS_KEY'))

# container info
containers = {}


def process(args, blob):
    logger.debug(blob.__dict__)
    logger.debug(blob.properties.__dict__)
    logger.debug(blob.properties.content_settings.__dict__)
    # {'content': '',
    #    'metadata': {'foo': 'bar'},
    #    'snapshot': None,
    #    'name': u'testing-20171031133540.txt',
    #    'properties': <azure.storage.blob.models.BlobProperties object at
    # # blob.properties
    # {'content_length': 8,
    #    'server_encrypted': True,
    #    'blob_type': 'BlockBlob',
    #    'blob_tier_inferred': True,
    #    'blob_tier': 'Hot',
    #    'append_blob_committed_block_count': None,
    #    'last_modified': datetime.datetime(2017, 10, 31, 20, 39, 36,
    #     tzinfo=tzutc()),
    #    'content_range': None,
    #    'etag': '"0x8D5209F803A286C"',
    #    'page_blob_sequence_number': None,
    #    'content_settings': <azure.storage.blob.models.ContentSettings
    #    'copy': <azure.storage.blob.models.CopyProperties object at
    #    'lease': <azure.storage.blob.models.LeaseProperties object at
    # # blob.properties.content_settings
    # {'content_language': None, 'content_encoding': None,
    #     'content_type': 'text/plain',
    #     'content_md5': '6xoyJ83D/tuuwv44v2wESg==',
    #     'content_disposition': None, 'cache_control': None}

    url = block_blob_service.make_blob_url(args.azure_container, blob.name)

    # TODO get container| storage_account region
    # if container not in containers:
    #     containers[container] = block_blob_service.get_container_metadata(
    #                                 container)

    _id = url
    _urls = [url]

    system_metadata = {}
    for field in ['server_encrypted', 'blob_type', 'blob_tier_inferred',
                  'blob_tier', 'append_blob_committed_block_count',
                  'content_range', 'etag', 'page_blob_sequence_number']:
        val = getattr(blob.properties, field, None)
        if val:
            system_metadata[field] = val

    system_metadata['eventType'] = 'ObjectCreated:Put'

    last_modified = str(blob.properties.last_modified).replace(' ', 'T')
    data_object = {
      "id": _id,
      "file_size": blob.properties.content_length,
      "created": last_modified,
      "updated": last_modified,
      # TODO check multipart md5 ?
      "checksum": blob.properties.content_settings.content_md5,
      "urls": _urls,
      "system_metadata": system_metadata,
      "user_metadata": blob.metadata
    }

    logger.debug(json.dumps(data_object))
    store(args, data_object)
    return True


def consume(args):
    # Get all the blobs
    for blob in block_blob_service.list_blobs(args.azure_container):
        blob_properties = block_blob_service.get_blob_properties(
                                            args.azure_container, blob.name)
        try:
            process(args, blob_properties)
        except AzureException as e:
            logger.exception(e)


def populate_args(argparser):
    """add arguments we expect """
    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='dos-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')

    argparser.add_argument('--azure_container', '-ac',
                           help='azure container name',
                           default='dos-testing')

    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')
    custom_args(argparser)


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume blobs from azure blob container, populate kafka')
    populate_args(argparser)
    args = argparser.parse_args()
    logger.debug(args)
    consume(args)
