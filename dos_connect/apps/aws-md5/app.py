from __future__ import print_function
from chalice import Chalice

import boto3
import hashlib


s3 = boto3.client('s3')
app = Chalice(app_name='aws-md5')

# read file 512K at a time
CHUNK_SIZE = 1024*512


def generate_chunks(result):
    """ read the result body a chunk at a time """
    for chunk in iter(lambda: result['Body'].read(CHUNK_SIZE), b''):
        yield chunk


@app.route('/{bucket_name}/{key}/md5sum')
def md5sum(bucket_name, key):
    """ calculate md5 for key in bucket """
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        hash = hashlib.md5()
        for chunk in generate_chunks(response):
            hash.update(chunk)
        return {'md5sum': hash.hexdigest()}
    except Exception as e:
        print(e)
        msg = 'Error getting object {} from bucket {}. Make sure they exist' \
              ' and your bucket is in the same region as this function.' \
              .format(key, bucket_name)
        return {'error': md5sum}
