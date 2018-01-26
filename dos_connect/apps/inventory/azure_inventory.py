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
from datetime import datetime

from customizations import store, custom_args
from .. import common_args, common_logging,  store, custom_args


BLOB_SERVICE = None


# Instantiates a storage client
def _blob_service():
    global BLOB_SERVICE
    if not BLOB_SERVICE:
        BLOB_SERVICE = BlockBlobService(
            account_name=os.environ.get('BLOB_STORAGE_ACCOUNT'),
            account_key=os.environ.get('BLOB_STORAGE_ACCESS_KEY'))
    return BLOB_SERVICE

# container info
containers = {}


def to_dos(url, blob):
    _id = url
    system_metadata = {}
    for field in ['server_encrypted', 'blob_type', 'blob_tier_inferred',
                  'blob_tier', 'append_blob_committed_block_count',
                  'content_range', 'etag', 'page_blob_sequence_number']:
        val = getattr(blob.properties, field, None)
        if val:
            system_metadata[field] = val

    system_metadata['event_type'] = 'ObjectCreated:Put'
    _urls = [{'url': url, 'system_metadata': system_metadata}]

    last_modified = blob.properties.last_modified
    return {
      "file_size": blob.properties.content_length,
      "created": last_modified.isoformat(),
      "updated": last_modified.isoformat(),
      # TODO check multipart md5 ?
      "checksums": [{"checksum": blob.properties.content_settings.content_md5,
                     'type': 'md5'}],
      "urls": _urls,
      "system_metadata": system_metadata,
      "user_metadata": blob.metadata
    }


def process(args, blob):

    url = _blob_service().make_blob_url(args.azure_container, blob.name)

    # TODO get container| storage_account region
    # if container not in containers:
    #     containers[container] = block_blob_service.get_container_metadata(
    #                                 container)
    data_object = to_dos(url, blob)

    store(args, data_object)
    return True


def consume(args):
    # Get all the blobs
    for blob in _blob_service().list_blobs(args.azure_container):
        blob_properties = _blob_service().get_blob_properties(
                                            args.azure_container, blob.name)
        try:
            process(args, blob_properties)
        except AzureException as e:
            logger.exception(e)


def populate_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--azure_container', '-ac',
                           help='azure container name',
                           default='dos-testing')

    common_args(argparser)
    custom_args(argparser)


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume blobs from azure blob container, populate store')
    populate_args(argparser)
    args = argparser.parse_args()
    common_logging(args)
    logger = logging.getLogger(__name__)
    logger.debug(args)
    consume(args)
