from kafka import KafkaProducer
from google.cloud import storage

import json
import argparse
import logging
import urllib
import time
import pprint
import sys
from customizations import store, custom_args
from .. import common_args, common_logging


def to_dos(bucket, record):
    system_metadata = {}
    for field in ["crc32c", "etag", "storageClass", "bucket", "generation"
                  "metageneration", "contentType"]:
        if field in record:
            system_metadata[field] = record[field]
    system_metadata['location'] = bucket.location
    system_metadata['event_type'] = 'ObjectCreated:Put'

    user_metadata = record.get('metadata', None)

    _id = record['id']
    _urls = [{
            'url': record['mediaLink'],
            "system_metadata": system_metadata,
            "user_metadata": user_metadata
        }]
    return {
      "id": _id,
      "file_size": int(record['size']),
      "created": record['timeCreated'],
      "updated": record['updated'],
      # TODO multipart ...
      "checksums": [{"checksum": record['md5Hash'], 'type': 'md5'}],
      "urls": _urls
    }


def process(args, bucket, record):
    if not record['kind'] == "storage#object":
        return True

    store(args, to_dos(bucket, record))
    return True


def populate_args(argparser):
    """add arguments we expect """
    argparser.add_argument('bucket_name',
                           help='''bucket_name to inventory''',
                           )
    common_args(argparser)
    custom_args(argparser)


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume blob info from gs, populate kafka')
    populate_args(argparser)

    args = argparser.parse_args()

    common_logging(args)

    logger = logging.getLogger(__name__)
    logger.debug(args)

    # Instantiates a client
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(args.bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        process(args, bucket, blob.__dict__['_properties'])
