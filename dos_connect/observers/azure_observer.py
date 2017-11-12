from azure.storage.queue import QueueService, QueueMessageFormat
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
from customizations import store, custom_args
from .. import common_args, common_logging


BLOB_SERVICE = None


# Instantiates a storage client
def _blob_service():
    if not BLOB_SERVICE:
        BLOB_SERVICE = BlockBlobService(
            account_name=os.environ.get('BLOB_STORAGE_ACCOUNT'),
            account_key=os.environ.get('BLOB_STORAGE_ACCESS_KEY'))
    return BLOB_SERVICE


def to_dos(message_json, blob=None):
    record = message_json['data']
    # get storage account, container and blob_name
    parsed_url = urlparse(record['url'])
    storage_account = parsed_url.netloc.split('.')[0]
    path = parsed_url.path.split('/')
    container = path[1]
    blob_name = '/'.join(path[(len(path)-2)*-1:])

    # only Microsoft.Storage.BlobCreated or Microsoft.Storage.BlobDeleted
    # no event raised for metadata update!
    event_methods = {
        'Microsoft.Storage.BlobDeleted': 'ObjectRemoved:Delete',
        'OBJECT_ARCHIVE': 'ObjectCreated:Copy',
        'Microsoft.Storage.BlobCreated': 'ObjectCreated:Put',
        'OBJECT_METADATA_UPDATE': 'ObjectModified'
    }

    # TODO get container region
    # if container not in containers:
    #     containers[container] = block_blob_service.get_container_metadata(
    #                                 container)

    _id = record['url']
    _url = record['url']
    system_metadata = {'event_type': event_methods[message_json['eventType']]}
    urls = [{'url': _url,
             'system_metadata': system_metadata,
             "user_metadata": {}}]

    data_object = {
      "id": _id,
      "urls": urls
    }

    if blob:
        for field in ['server_encrypted', 'blob_type', 'blob_tier_inferred',
                      'blob_tier', 'append_blob_committed_block_count',
                      'content_range', 'etag', 'page_blob_sequence_number']:
            val = getattr(blob.properties, field, None)
            if val:
                system_metadata[field] = val
        last_modified = str(blob.properties.last_modified).replace(' ', 'T')
        data_object = {
          "id": _id,
          "file_size": blob.properties.content_length,
          "created": last_modified,
          "updated": last_modified,
          "mime_type": blob.properties.content_settings.content_type,
          # TODO check multipart md5 ?
          "checksums": [{"checksum": blob.properties.content_settings.content_md5, 'type': 'md5'}],  # NOQA
          "urls": urls
        }

    return data_object


def process(args, message):

    message_json = json.loads(message.content)
    if not message_json['eventType'].startswith('Microsoft.Storage'):
        return True
    data_object = to_dos(message_json)
    if message_json['eventType'] == 'Microsoft.Storage.BlobCreated':
        # get blob info
        blob = _blob_service().get_blob_properties(container, blob_name)
        data_object = to_dos(message_json, blob)

    store(args, data_object)
    return True


def consume(args):
    # Get the service resources

    queue_service = QueueService(
                        account_name=os.environ.get('QUEUE_STORAGE_ACCOUNT'),
                        account_key=os.environ.get('QUEUE_STORAGE_ACCESS_KEY'))

    queue_service.decode_function = QueueMessageFormat.binary_base64decode

    logger.debug('Listening for messages on {}'.format(args.azure_queue))
    while True:
        messages = queue_service.get_messages(args.azure_queue,
                                              num_messages=16,
                                              visibility_timeout=args.wait_time
                                              )
        for message in messages:
            try:
                process(args, message)
            except AzureException as e:
                logger.exception(e)
            if not args.dry_run:
                logger.debug('deleting message {}'.format(message.id))
                queue_service.delete_message(args.azure_queue,
                                             message.id, message.pop_receipt)
        time.sleep(args.wait_time)


def populate_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--azure_queue', '-aq',
                           help='azure queue name',
                           default='dos-testing')

    argparser.add_argument('--wait_time', '-wt',
                           help='time to wait between fetches',
                           default=5)

    common_args(argparser)
    custom_args(argparser)

if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume events from azure storage queue, populate store')
    populate_args(argparser)
    args = argparser.parse_args()
    common_logging(args)
    logger = logging.getLogger(__name__)

    logger.debug(args)
    consume(args)
