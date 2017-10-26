#!/usr/bin/env python
import os
import sys
import json
import boto3
import logging
import argparse
import urllib
from kafka import KafkaProducer
from botocore.client import Config
from urlparse import urlparse

logger = logging.getLogger('s3_inventory')


class KafkaHandler(object):

    """Creates DOS object on kafka queue in response to matched events."""

    def __init__(self,
                 kafka_topic=None, kafka_bootstrap=None,
                 dry_run=False):
        super(KafkaHandler, self).__init__()
        self.kafka_topic = kafka_topic
        self.kafka_bootstrap = kafka_bootstrap
        self.dry_run = dry_run
        logger.debug(
            'kafka_topic:{} kafka_bootstrap:{}'
            .format(kafka_topic, kafka_bootstrap))

    def on_any_event(self, endpoint_url, region, bucket_name, record):
        try:
            self.process(endpoint_url, region, bucket_name, record)
        except Exception as e:
            logger.exception(e)

    def process(self, endpoint_url, region, bucket_name, record):
        """
        {u'LastModified':
            datetime.datetime(2017, 10, 23, 16, 20, 45, tzinfo=tzutc()),
        u'ETag': '"d3b3a66c7235c6b09a55a626861f5f91"',
        u'StorageClass': 'STANDARD',
        u'Key': 'passport photo.JPG', u'Size': 341005}
        """
        _event_type = 'ObjectCreated:Put'

        _id = record['Key']
        _id_parts = _id.split('/')
        _id_parts[-1] = urllib.quote_plus(_id_parts[-1])
        _id = '/'.join(_id_parts)

        _url = "s3://{}.s3-{}.amazonaws.com/{}".format(
                  bucket_name, region, _id)
        if endpoint_url:
            parsed = urlparse(endpoint_url)
            _url = 's3://{}/{}/{}'.format(parsed.netloc, bucket_name,  _id)
        _system_metadata_fields = {
            'StorageClass': record['StorageClass'],
            "event_type": _event_type,
            "bucket_name": bucket_name
        }
        etag = record['ETag']
        if etag.startswith('"') and etag.endswith('"'):
            etag = etag[1:-1]
        data_object = {
          "id": _id,
          "file_size": record['Size'],
          # The time, in ISO-8601,when S3 finished processing the request,
          "created":  record['LastModified'].isoformat(),
          "updated":  record['LastModified'].isoformat(),
          # TODO multipart ...
          # https://forums.aws.amazon.com/thread.jspa?messageID=203436&#203436
          "checksum": etag, 
          "urls": [_url],
          "system_metadata_fields": _system_metadata_fields
        }
        self.to_kafka(data_object)

    def to_kafka(self, payload):
        """ write dict to kafka """
        key = '{}~{}'.format(payload['system_metadata_fields']['event_type'],
                             payload['urls'][0])
        if self.dry_run:
            logger.debug(key)
            logger.debug(payload)
            return
        producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap)
        producer.send(args.kafka_topic, key=key, value=json.dumps(payload))
        producer.flush()
        logger.debug('sent to kafka: {} {}'.format(self.kafka_topic, key))


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        description='Consume events from bucket, populate kafka')

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

    argparser.add_argument('--endpoint_url', '-ep',
                           help='''for swift, ceph and other non-aws endpoints''',
                           default=None)

    argparser.add_argument('bucket_name',
                           help='''bucket_name to inventory''',
                           )

    args = argparser.parse_args()

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    logger.debug(args)
    event_handler = KafkaHandler(
        kafka_topic=args.kafka_topic,
        kafka_bootstrap=args.kafka_bootstrap,
        dry_run=args.dry_run,
    )

    # boto3.client('s3', 'us-west-2', config=Config(s3={'addressing_style': 'path'}))

    # support non aws hosts
    if args.endpoint_url:
        use_ssl = True
        if args.endpoint_url.startswith('http://'):
            use_ssl = False
        client = boto3.client(
            's3', endpoint_url=args.endpoint_url, use_ssl=use_ssl,
            config=Config(s3={'addressing_style': 'path'}, signature_version='s3')
        )
    else:
        client = boto3.client('s3')
    paginator = client.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=args.bucket_name)
    for page in page_iterator:
        logger.debug(page)
        region = None
        if 'x-amz-bucket-region' in page['ResponseMetadata']['HTTPHeaders']:
            region = page['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']
        for record in page['Contents']:
            logger.debug(record)
            event_handler.on_any_event(args.endpoint_url, region, args.bucket_name, record)
