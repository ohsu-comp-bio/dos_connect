from kafka import KafkaProducer
from google.cloud import pubsub
from google.cloud import storage

import json
import argparse
import logging
import urllib
import time
import pprint

logger = logging.getLogger('pubsub-notifications')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


# Instantiates a client
storage_client = storage.Client()
# bucket info
buckets = {}


def to_kafka(args, payload):
    """ write dict to kafka """
    key = '{}~{}'.format(payload['system_metadata']['eventType'],
                         payload['urls'][0])

    if not args.dry_run:
        producer = KafkaProducer(bootstrap_servers=args.kafka_bootstrap)
        producer.send(args.kafka_topic, key=key, value=json.dumps(payload))
        producer.flush()
        logger.debug('sent to kafka topic: {}'.format(args.kafka_topic))
    else:
        logger.debug('dry_run to kafka topic: {} {}'
                     .format(args.kafka_topic, key))


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

    record = json.loads(message.data)
    if not record['kind'] == "storage#object":
        return True

    bucketId = message.attributes['bucketId']
    if bucketId not in buckets:
        buckets[bucketId] = storage_client.get_bucket(bucketId)

    system_metadata = dict(message.attributes)
    for field in ["crc32c", "etag", "storageClass", "bucket", "generation"
                  "metageneration", "contentType"]:
        if field in record:
            system_metadata[field] = record[field]
    system_metadata['location'] = buckets[bucketId].location
    # https://cloud.google.com/storage/docs/pubsub-notifications#events
    event_methods = {
        'OBJECT_DELETE': 'ObjectRemoved:Delete',
        'OBJECT_ARCHIVE': 'ObjectCreated:Copy',
        'OBJECT_FINALIZE': 'ObjectCreated:Put',
        'OBJECT_METADATA_UPDATE': 'ObjectModified'
    }
    system_metadata['eventType'] = event_methods[system_metadata['eventType']]

    user_metadata = record.get('metadata', None)

    _id = record['id']
    _urls = [record['mediaLink']]
    data_object = {
      "id": _id,
      "file_size": int(record['size']),
      "created": record['timeCreated'],
      "updated": record['updated'],
      # TODO multipart ...
      # https://cloud.google.com/storage/docs/hashes-etags#_MD5
      "checksum": record['md5Hash'],
      "urls": _urls,
      "system_metadata": system_metadata,
      "user_metadata": user_metadata
    }
    # logger.debug(system_metadata.__class__)
    # logger.debug(type(system_metadata))
    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(system_metadata)
    logger.debug(json.dumps(data_object))
    to_kafka(args, data_object)
    return True


def consume(args):
    # Get the service resources

    subscriber = pubsub.SubscriberClient()
    # TODO - figure out how to dynamically create subscriptions
    # topic_name = 'projects/{project_id}/topics/{topic}'.format(
    #     project_id=args.google_cloud_project,
    #     topic=args.google_topic,
    # )
    # sub_name = 'projects/{project_id}/subscriptions/{sub}'.format(
    #     project_id=args.google_cloud_project,
    #     sub=args.google_subscription_name,
    # )
    # logger.debug(topic_name)
    # logger.debug(sub_name)
    # subscription = subscriber.create_subscription(topic_name, sub_name)

    subscription_path = subscriber.subscription_path(
        args.google_cloud_project, args.google_subscription_name)

    # sub_name = 'projects/elite-impact-184313/topics/dos-testing'
    # subscription = subscriber.subscribe(sub_name)

    def callback(message):
        try:
            # logger.debug(message.attributes)
            # logger.debug(message.data)
            process(args, message)
            if not args.dry_run:
                message.ack()
        except Exception as e:
            logger.exception(e)

    subscriber.subscribe(subscription_path, callback=callback)

    # subscription.open(callback)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    logger.debug('Listening for messages on {}'.format(subscription_path))
    while True:
        time.sleep(60)


def populate_args(argparser):
    """add arguments we expect """
    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='s3-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')

    argparser.add_argument('--google_cloud_project', '-kp',
                           help='project id',
                           default='elite-impact-184313')

    argparser.add_argument('--google_topic', '-gt',
                           help='pubsub queue name',
                           default='dos-testing')

    argparser.add_argument('--google_subscription_name', '-gs',
                           help='pubsub subscription name',
                           default='dos-testing')

    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume events from aws s3, populate kafka')
    populate_args(argparser)
    args = argparser.parse_args()
    consume(args)
