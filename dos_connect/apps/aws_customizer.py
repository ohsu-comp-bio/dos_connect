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
    logger.error(kwargs)
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
