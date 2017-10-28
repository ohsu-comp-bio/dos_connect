from kafka import KafkaProducer
from google.cloud import storage

import json
import argparse
import logging
import urllib
import time
import pprint

logger = logging.getLogger('gs-inventory')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


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


def process(args, bucket, record):
    if not record['kind'] == "storage#object":
        return True

    system_metadata = {}
    for field in ["crc32c", "etag", "storageClass", "bucket", "generation"
                  "metageneration", "contentType"]:
        if field in record:
            system_metadata[field] = record[field]
    system_metadata['location'] = bucket.location
    system_metadata['eventType'] = 'ObjectCreated:Put'

    user_metadata = record['metadata']

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


def populate_args(argparser):
    """add arguments we expect """
    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='s3-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')

    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')

    argparser.add_argument('bucket_name',
                           help='''bucket_name to inventory''',
                           )


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume blob info from gs, populate kafka')
    populate_args(argparser)
    args = argparser.parse_args()
    # Instantiates a client
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(args.bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        process(args, bucket, blob.__dict__['_properties'])
