""" default client app plugins """
import requests
import logging
import os

logger = logging.getLogger(__name__)
aws_md5_url = os.getenv('AWS_MD5_URL', None)
assert aws_md5_url, 'Please set AWS_MD5_URL env var'


def user_metadata(**kwargs):
    """ noop return user metadata """
    return None


def before_store(**kwargs):
    """ noop modify data_object """
    pass


def md5sum(**kwargs):
    """ return md5 by calling our lambda """
    etag = kwargs.get('etag', None)
    bucket_name = kwargs.get('bucket_name', None)
    key = kwargs.get('key', None)
    etag_parts = etag.split('-')
    if len(etag_parts) == 1:
        return etag

    url = '{}/{}/{}/md5sum'.format(aws_md5_url, bucket_name, key)
    response = requests.get(url).json()
    logger.error(response)
    assert 'md5sum' in response
    return response['md5sum']


def id(**kwargs):
    """ use the checksum as the key """
    print kwargs
    data_object = kwargs.get('data_object', None)
    logger.error('id')
    logger.error(data_object)
    return data_object.checksums[0].checksum
