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


def process(args, bucket, record):
    if not record['kind'] == "storage#object":
        return True

    logger.debug(record)
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
    data_object = {
      "id": _id,
      "file_size": int(record['size']),
      "created": record['timeCreated'],
      "updated": record['updated'],
      # TODO multipart ...
      "checksums": [{"checksum": record['md5Hash'], 'type': 'md5'}],
      "urls": _urls
    }
    # logger.debug(system_metadata.__class__)
    # logger.debug(type(system_metadata))
    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(system_metadata)
    logger.debug(json.dumps(data_object))
    store(args, data_object)
    return True


def populate_args(argparser):
    """add arguments we expect """
    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')

    argparser.add_argument("-v", "--verbose", help="increase output verbosity",
                           default=False,
                           action="store_true")

    argparser.add_argument('bucket_name',
                           help='''bucket_name to inventory''',
                           )
    custom_args(argparser)


if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume blob info from gs, populate kafka')
    populate_args(argparser)

    args = argparser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    logger = logging.getLogger(__name__)
    logger.debug(args)

    # Instantiates a client
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(args.bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        process(args, bucket, blob.__dict__['_properties'])
