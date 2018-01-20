import json
import boto3
import argparse
import logging
import urllib
import sys
from .. import common_args, common_logging,  store, custom_args, md5sum
from datetime import datetime

# Boto3 will check these environment variables for credentials:
# AWS_ACCESS_KEY_ID The access key for your AWS account.
# AWS_SECRET_ACCESS_KEY The secret key for your AWS account.
# so to run it:
# AWS_ACCESS_KEY_ID=. AWS_SECRET_ACCESS_KEY=. \
#  AWS_DEFAULT_REGION=us-west-2 \
#  python sqs_consumer.py
# mainipulate the bucket via
# AWS_ACCESS_KEY_ID=. AWS_SECRET_ACCESS_KEY=. aws s3 cp text  s3://dos-testing


def to_dos(record):
    """ given a message from the source, map to a new data_object """
    system_metadata = {}
    system_metadata['awsRegion'] = record['awsRegion']
    s3 = record['s3']
    system_metadata['bucket_name'] = s3['bucket']['name']
    system_metadata['principalId'] = \
        s3["bucket"]["ownerIdentity"]["principalId"]
    system_metadata['event_type'] = record["eventName"]
    obj = s3['object']

    user_metadata = {}
    _id = urllib.quote_plus(obj['key'])
    _url = "s3://{}.s3-{}.amazonaws.com/{}".format(
              system_metadata['bucket_name'],
              record['awsRegion'],
              _id
              )
    _url = {
        'url': _url,
        "system_metadata": system_metadata,
        "user_metadata": user_metadata,
    }
    eventTime = datetime.strptime(record['eventTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
    data_object = {
      "file_size": obj.get('size', None),
      # The time, in ISO-8601,when S3 finished processing the request,
      "created": eventTime.isoformat(),
      "updated": eventTime.isoformat(),
      # TODO multipart ...
      # https://forums.aws.amazon.com/thread.jspa?messageID=203436&#203436
      "checksums": [{'checksum': md5sum(key=obj['key'],
                                        bucket_name=system_metadata['bucket_name'],
                                        etag=obj.get('eTag', None)),
                     'type': 'md5'}],
      # http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro
      "urls": [_url],
    }
    return data_object


def process(args, message):
    """
    http://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """
    # we need a call to s3 to fetch metadata not in queue message
    client = boto3.client('s3')

    logger.debug(message.body)
    sqs_json = message.body
    sqs = json.loads(sqs_json)

    if 'Records' not in sqs:
        return True
    for record in sqs['Records']:
        if not record['eventSource'] == "aws:s3":
            continue
        s3 = record['s3']
        key = s3['object']['key']
        bucket_name = s3['bucket']['name']
        data_object = to_dos(record)
        if not (data_object['urls'][0]['system_metadata']['event_type'] ==
                "ObjectRemoved:Delete"):
            try:
                head = client.head_object(Bucket=bucket_name,
                                          Key=key)
                if ('Metadata' in head):
                    data_object['urls'][0]['user_metadata'] = head['Metadata']
            except Exception as e:
                logger.info("head failed. {} {} {}"
                            .format(bucket_name, key, e))

        store(args, data_object)
    return True


def consume(args):
    # Get the service resources
    sqs = boto3.resource('sqs')

    # Get the queue. This returns an SQS.Queue instance
    queue = sqs.get_queue_by_name(QueueName=args.sqs_queue_name)

    # You can now access identifiers and attributes
    logger.debug('Starting infinite loop for {}'.format(queue.url))

    while True:
        try:
            for message in queue.receive_messages(WaitTimeSeconds=20):
                # Get the custom author message attribute if it was set
                # Print out the body and author (if set)
                if process(args, message):
                    message.delete()
        except Exception as e:
            logger.exception(e)


def populate_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--sqs_queue_name', '-qn',
                           help='sqs queue name',
                           default='dos-testing')
    common_args(argparser)
    custom_args(argparser)

if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume events from aws s3, populate store')
    populate_args(argparser)
    args = argparser.parse_args()
    common_logging(args)
    logger = logging.getLogger(__name__)
    consume(args)
