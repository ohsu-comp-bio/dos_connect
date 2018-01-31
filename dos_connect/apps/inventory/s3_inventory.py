#!/usr/bin/env python
import os
import sys
import json
import boto3
import logging
import argparse
import urllib
from botocore.client import Config
from urlparse import urlparse
from .. import common_args, common_logging,  store, custom_args, md5sum

logger = logging.getLogger('s3_inventory')


def to_dos(endpoint_url, region, bucket_name, record, metadata):
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

        _system_metadata = {
            'StorageClass': record['StorageClass'],
            "event_type": _event_type,
            "bucket_name": bucket_name
        }
        _url = {
            'url': _url,
            "system_metadata": _system_metadata,
            "user_metadata": metadata,
        }
        etag = record['ETag']
        if etag.startswith('"') and etag.endswith('"'):
            etag = etag[1:-1]
        if etag.startswith('%22') and etag.endswith('%22'):
            etag = etag[3:-3]
        return {
          "file_size": record['Size'],
          # The time, in ISO-8601,when S3 finished processing the request,
          "created":  record['LastModified'].isoformat(),
          "updated":  record['LastModified'].isoformat(),
          # TODO multipart ...
          "checksums": [{'checksum': md5sum(etag=etag,
                         bucket_name=bucket_name, key=_id), 'type': 'md5'}],
          "urls": [_url]
        }


class DOSHandler(object):

    """Creates DOS object in store in response to matched events."""

    def __init__(self,
                 args=None):
        super(DOSHandler, self).__init__()
        self.dry_run = args.dry_run

    def on_any_event(self, endpoint_url, region, bucket_name, record,
                     metadata):
        try:
            self.process(endpoint_url, region, bucket_name, record, metadata)
        except Exception as e:
            logger.exception(e)

    def process(self, endpoint_url, region, bucket_name, record, metadata):
        data_object = to_dos(endpoint_url, region, bucket_name, record,
                             metadata)
        store(args, data_object)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        description='Consume events from bucket, populate store')
    argparser.add_argument('--endpoint_url', '-ep',
                           help='''for swift, ceph, other non-aws endpoints''',
                           default=None)
    argparser.add_argument('bucket_name',
                           help='''bucket_name to inventory''',
                           )
    common_args(argparser)
    custom_args(argparser)

    args = argparser.parse_args()

    common_logging(args)
    event_handler = DOSHandler(args)

    # support non aws hosts
    if args.endpoint_url:
        use_ssl = True
        if args.endpoint_url.startswith('http://'):
            use_ssl = False
        client = boto3.client(
            's3', endpoint_url=args.endpoint_url, use_ssl=use_ssl,
            config=Config(s3={'addressing_style': 'path'},
                          signature_version='s3')
        )
    else:
        client = boto3.client('s3')
    paginator = client.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=args.bucket_name)
    for page in page_iterator:
        region = None
        if 'x-amz-bucket-region' in page['ResponseMetadata']['HTTPHeaders']:
            region = page['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']
        for record in page['Contents']:
            logger.debug(record)
            head = client.head_object(Bucket=args.bucket_name,
                                      Key=record['Key'])
            metadata = head['Metadata'] if ('Metadata' in head) else None
            event_handler.on_any_event(args.endpoint_url, region,
                                       args.bucket_name, record, metadata)
