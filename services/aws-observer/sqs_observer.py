import json
import boto3
import argparse
import logging
import urllib
from customizations import store, custom_args
import sys


# Boto3 will check these environment variables for credentials:
# AWS_ACCESS_KEY_ID The access key for your AWS account.
# AWS_SECRET_ACCESS_KEY The secret key for your AWS account.
# so to run it:
# AWS_ACCESS_KEY_ID=. AWS_SECRET_ACCESS_KEY=. \
#  AWS_DEFAULT_REGION=us-west-2 \
#  python sqs_consumer.py
# mainipulate the bucket via
# AWS_ACCESS_KEY_ID=. AWS_SECRET_ACCESS_KEY=. aws s3 cp text  s3://dos-testing


def process(args, message):
    """
    http://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """
    logger.debug(message.body)
    sqs_json = message.body
    sqs = json.loads(sqs_json)
    # we need a call to s3 to fetch metadata not in queue message
    client = boto3.client('s3')

    if 'Records' not in sqs:
        return True
    for record in sqs['Records']:
        if not record['eventSource'] == "aws:s3":
            continue
        system_metadata = {}
        system_metadata['awsRegion'] = record['awsRegion']
        s3 = record['s3']
        system_metadata['bucket_name'] = s3['bucket']['name']
        system_metadata['principalId'] = \
            s3["bucket"]["ownerIdentity"]["principalId"]
        system_metadata['event_type'] = record["eventName"]
        obj = s3['object']

        user_metadata = {}
        if not system_metadata['event_type'] == "ObjectRemoved:Delete":
            try:
                head = client.head_object(Bucket=s3['bucket']['name'],
                                          Key=obj['key'])
                user_metadata = head['Metadata'] if ('Metadata' in head) else None
            except Exception as e:
                logger.info("head failed. {} {} {}".format(s3['bucket']['name'], obj['key'], e))

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
        data_object = {
          "id": _id,
          "file_size": obj.get('size', None),
          # The time, in ISO-8601,when S3 finished processing the request,
          "created": record['eventTime'],
          "updated": record['eventTime'],
          # TODO multipart ...
          # https://forums.aws.amazon.com/thread.jspa?messageID=203436&#203436
          "checksums": [{'checksum': obj.get('eTag', None), 'type': 'md5'}],
          # http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro
          "urls": [_url],
        }
        logger.debug(json.dumps(data_object))
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
            logger.error(e)


def populate_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--sqs_queue_name', '-qn',
                           help='''sqs queue name''',
                           default='dos-testing')
    argparser.add_argument("-v", "--verbose", help="increase output verbosity",
                           default=False,
                           action="store_true")
    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')
    custom_args(argparser)

if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume events from aws s3, populate store')
    populate_args(argparser)
    args = argparser.parse_args()
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger(__name__)
    consume(args)
