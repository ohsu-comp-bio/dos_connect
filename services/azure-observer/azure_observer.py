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

logger = logging.getLogger('azure-notifications')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


# Instantiates a storage client
block_blob_service = BlockBlobService(
                        account_name=os.environ.get('BLOB_STORAGE_ACCOUNT'),
                        account_key=os.environ.get('BLOB_STORAGE_ACCESS_KEY'))

# container info
containers = {}


def process(args, message):

    message_json = json.loads(message.content)
    # {
    #   "topic":"/subscriptions/68106052-6b47-46b3-bd47-0cd668b9b500/resourceGroups/dostesting/providers/Microsoft.Storage/storageAccounts/dostesting",
    #   "subject":"/blobServices/default/containers/dos-testing/blobs/testing-20171031073707.txt",
    #   "eventType":"Microsoft.Storage.BlobCreated",
    #   "eventTime":"2017-10-31T14:39:20.415Z",
    #   "id":"23377130-001e-0019-5456-52940906bd44",
    #   "data":{
    #     "api":"PutBlob",
    #     "clientRequestId":"46896a98-be49-11e7-bbfa-acbc32be6b2d",
    #     "requestId":"23377130-001e-0019-5456-529409000000",
    #     "eTag":"0x8D5206D2BFA8492",
    #     "contentType":"text/plain",
    #     "contentLength":8,
    #     "blobType":"BlockBlob",
    #     "url":"https://dostesting.blob.core.windows.net/dos-testing/testing-20171031073707.txt",
    #     "sequencer":"00000000000027AE00000000002C92E3",
    #     "storageDiagnostics":{
    #       "batchId":"8483f333-0ab2-4bec-a23b-90ae8f0465c3"
    #     }
    #   }
    # }

    if not message_json['eventType'].startswith('Microsoft.Storage'):
        return True
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
    _urls = [record['url']]

    if message_json['eventType'] == 'Microsoft.Storage.BlobCreated':
        # get blob info
        blob = block_blob_service.get_blob_properties(container, blob_name)
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
        #

        system_metadata = {}
        for field in ['server_encrypted', 'blob_type', 'blob_tier_inferred',
                      'blob_tier', 'append_blob_committed_block_count',
                      'content_range', 'etag', 'page_blob_sequence_number']:
            val = getattr(blob.properties, field, None)
            if val:
                system_metadata[field] = val

        system_metadata['eventType'] = event_methods[message_json['eventType']]

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
    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='dos-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')

    argparser.add_argument('--azure_queue', '-aq',
                           help='azure queue name',
                           default='dos-testing')

    argparser.add_argument('--wait_time', '-wt',
                           help='time to wait between fetches',
                           default=5)

    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')
    custom_args(argsparser)

if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume events from azure storage queue, populate kafka')
    populate_args(argparser)
    args = argparser.parse_args()
    logger.debug(args)
    consume(args)
