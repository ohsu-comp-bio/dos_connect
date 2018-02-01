#!/usr/bin/env python
import os
import sys
import json
import swiftclient.client as swiftclient
import logging
import argparse
import urllib
from urlparse import urlparse
from .. import common_args, common_logging,  store, custom_args, md5sum
from . import get_offset, save_offset

logger = logging.getLogger('s3_inventory')


def to_dos(endpoint_url, region, bucket_name, record, metadata):
        """
        {u'last_modified': u'2018-02-01T01:15:39.623630',
         u'hash': u'7ddfbd9eafcd73c68ad72d1a792c96bb',
         u'name': u'test/ttt',
         u'content_type': u'application/octet-stream',
         u'x-object-meta-foo': u'bar',
         u'bytes': 169}
        """
        _event_type = 'ObjectCreated:Put'

        _id = record['name']
        _id_parts = _id.split('/')
        _id_parts[-1] = urllib.quote_plus(_id_parts[-1])
        _id = '/'.join(_id_parts)

        _url = "s3://{}.s3-{}.amazonaws.com/{}".format(
                  bucket_name, region, _id)
        if endpoint_url:
            parsed = urlparse(endpoint_url)
            _url = 's3://{}/{}/{}'.format(parsed.netloc, bucket_name,  _id)

        _system_metadata = {
            "event_type": _event_type,
            "bucket_name": bucket_name
        }
        _url = {
            'url': _url,
            "system_metadata": _system_metadata,
            "user_metadata": metadata,
        }
        etag = record['hash']
        if etag.startswith('"') and etag.endswith('"'):
            etag = etag[1:-1]
        if etag.startswith('%22') and etag.endswith('%22'):
            etag = etag[3:-3]
        return {
          "file_size": record['bytes'],
          # The time, in ISO-8601,when S3 finished processing the request,
          "created":  record['last_modified'],
          "updated":  record['last_modified'],
          # multipart ...
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
            save_offset({'name': record['name']})
        except Exception as e:
            logger.exception(e)

    def process(self, endpoint_url, region, bucket_name, record, metadata):
        data_object = to_dos(endpoint_url, region, bucket_name, record,
                             metadata)
        store(args, data_object)


if __name__ == "__main__":
    # setup ...
    argparser = argparse.ArgumentParser(
        description='Consume events from bucket, populate store')
    argparser.add_argument('--endpoint_url', '-ep',
                           help='swift storage url i.e. '
                           'http://XXX/v1/AUTH_xxxxxxx',
                           default=None)
    argparser.add_argument('bucket_name',
                           help='bucket_name to inventory',
                           )
    SWIFT_AUTH_TOKEN = os.getenv('SWIFT_AUTH_TOKEN', None)
    argparser.add_argument('--auth_token', '-t',
                           help='swift auth_token `openstack token issue` '
                           'SWIFT_AUTH_TOKEN',
                           default=SWIFT_AUTH_TOKEN)

    common_args(argparser)
    custom_args(argparser)

    args = argparser.parse_args()

    common_logging(args)

    # our handler
    event_handler = DOSHandler(args)

    # get connection
    swift = swiftclient.Connection(preauthurl=args.endpoint_url,
                                   preauthtoken=args.auth_token,
                                   auth_version="2.0")

    # do we have a saved offset?
    offset = get_offset()
    last_name = None
    if offset:
        last_name = offset['name']

    (container, objects) = swift.get_container(args.bucket_name,
                                               marker=last_name,
                                               full_listing=True)

    # iterate through objects
    for obj in objects:
        # need a separate call to get meta :-(
        headers = swift.head_object(container=args.bucket_name,
                                    obj=obj['name'])
        metadata = [{k: headers[k]} for k in headers if k.startswith('x-object-meta-')]  # noqa
        event_handler.on_any_event(args.endpoint_url, None,
                                   args.bucket_name, obj, metadata)
