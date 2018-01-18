from google.cloud import pubsub
from google.cloud import storage

import json
import argparse
import logging
import urllib
import time
from datetime import datetime
import pprint
import sys
from .. import common_args, common_logging,  store, custom_args


# Instantiates a client
STORAGE_CLIENT = None
# bucket info
buckets = {}


def _client():
    global STORAGE_CLIENT
    if not STORAGE_CLIENT:
        STORAGE_CLIENT = storage.Client()
    return STORAGE_CLIENT


def to_dos(message):
    record = json.loads(message.data)
    if not record['kind'] == "storage#object":
        return None
    system_metadata = dict(message.attributes)
    for field in ["crc32c", "etag", "storageClass", "bucket", "generation"
                  "metageneration", "contentType"]:
        if field in record:
            system_metadata[field] = record[field]
    # https://cloud.google.com/storage/docs/pubsub-notifications#events
    event_methods = {
        'OBJECT_DELETE': 'ObjectRemoved:Delete',
        'OBJECT_ARCHIVE': 'ObjectCreated:Copy',
        'OBJECT_FINALIZE': 'ObjectCreated:Put',
        'OBJECT_METADATA_UPDATE': 'ObjectModified'
    }
    system_metadata['event_type'] = event_methods[system_metadata['eventType']]

    user_metadata = record.get('metadata', None)

    _id = record['id']
    _urls = [{'url': record['mediaLink'],
              'system_metadata': system_metadata,
              'user_metadata': user_metadata
              }]
    return {
      "id": _id,
      "file_size": int(record['size']),
      "created": datetime.strptime(record['timeCreated'], "%Y-%m-%dT%H:%M:%S.%fZ"),
      "updated": datetime.strptime(record['updated'], "%Y-%m-%dT%H:%M:%S.%fZ"),
      # TODO multipart ...
      # https://cloud.google.com/storage/docs/hashes-etags#_MD5
      "checksums": [{"checksum": record['md5Hash'], 'type': 'md5'}],
      "urls": _urls
    }


def process(args, message):
    # https://cloud.google.com/storage/docs/reporting-changes
    # https://cloud.google.com/storage/docs/json_api/v1/objects
    # {u'resource':
    #  u'projects/_/buckets/dos-testing/objects/testing.txt#1509217572944932',
    #  u'objectId': u'testing.txt', u'bucketId': u'dos-testing',
    #  u'notificationConfig':
    #     u'projects/_/buckets/dos-testing/notificationConfigs/5',
    #  u'payloadFormat': u'JSON_API_V1', u'eventType': u'OBJECT_DELETE',
    #  u'objectGeneration': u'1509217572944932'}
    #
    # {
    #   "kind": "storage#object",
    #   "id": "dos-testing/testing.txt/1509217572944932",
    #   "selfLink":
    #     "https://www.googleapis.com/storage/v1/b/dos-testing/o/testing.txt",
    #   "name": "testing.txt",
    #   "bucket": "dos-testing",
    #   "generation": "1509217572944932",
    #   "metageneration": "2",
    #   "contentType": "text/plain",
    #   "timeCreated": "2017-10-28T19:06:12.939Z",
    #   "updated": "2017-10-28T19:07:08.062Z",
    #   "storageClass": "REGIONAL",
    #   "timeStorageClassUpdated": "2017-10-28T19:06:12.939Z",
    #   "size": "873",
    #   "md5Hash": "blJQo/K03yZsMWugyHv5EQ==",
    #   "mediaLink": "https://www.googleapis.com/download/storage/v1/b/dos-testing/o/testing.txt?generation=1509217572944932&alt=media",  # NOQA
    #   "metadata": {
    #     "foo": "bar"
    #   },
    #   "crc32c": "DAxGUg==",
    #   "etag": "CKT4y8qBlNcCEAI="
    # }

    data_object = to_dos(message)
    if data_object:
        bucketId = message.attributes['bucketId']
        if bucketId not in buckets:
            buckets[bucketId] = _client().get_bucket(bucketId)
        data_object['urls'][0]['system_metadata']['location'] = buckets[bucketId].location
        store(args, data_object)
        return True


def consume(args):
    # Get the service resources

    subscriber = pubsub.SubscriberClient()

    topic_path = subscriber.topic_path(args.google_cloud_project,
                                       args.google_topic)

    subscription_path = subscriber.subscription_path(
        args.google_cloud_project, args.google_subscription_name)

    def callback(message):
        try:
            # logger.debug(message.attributes)
            # logger.debug(message.data)
            process(args, message)
            if not args.dry_run:
                message.ack()
        except Exception as e:
            logger.exception(e)

    # subscription needs to exist. see
    # https://cloud.google.com/pubsub/docs/admin#create_a_pull_subscription
    subscription = subscriber.subscribe(subscription_path, callback=callback)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    logger.info('Listening for messages on {}'.format(subscription_path))
    while True:
        time.sleep(60)


def populate_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--google_cloud_project', '-kp',
                           help='project id', required=True)

    argparser.add_argument('--google_topic', '-gt',
                           help='pubsub queue name', required=True)

    argparser.add_argument('--google_subscription_name', '-gs',
                           help='pubsub subscription name', required=True)

    common_args(argparser)
    custom_args(argparser)


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume events from aws s3, populate server')
    populate_args(argparser)
    args = argparser.parse_args()
    common_logging(args)
    logger = logging.getLogger(__name__)

    consume(args)
