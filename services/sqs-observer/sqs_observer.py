from kafka import KafkaProducer
import json
import boto3
import argparse

import logging
logger = logging.getLogger('sqs_observer')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

# Boto3 will check these environment variables for credentials:
# AWS_ACCESS_KEY_ID The access key for your AWS account.
# AWS_SECRET_ACCESS_KEY The secret key for your AWS account.
# so to run it:
# AWS_ACCESS_KEY_ID=. AWS_SECRET_ACCESS_KEY=. \
#  AWS_DEFAULT_REGION=us-west-2 \
#  python sqs_consumer.py
# mainipulate the bucket via
# AWS_ACCESS_KEY_ID=. AWS_SECRET_ACCESS_KEY=. aws s3 cp text  s3://dos-testing

def to_kafka(args, payload):
    """ write dict to kafka """
    producer = KafkaProducer(bootstrap_servers=args.kafka_bootstrap)
    key = '{}~{}~{}'.format(payload['system_metadata_fields']['event_type'],
                            payload['system_metadata_fields']['bucket_name'],
			    payload.get('checksum', None))
    producer.send(args.kafka_topic, key=key, value=json.dumps(payload))
    producer.flush()
    logger.debug('sent to kafka topic: {}'.format(args.kafka_topic))


def process(args, message):
    """
    http://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """
    logger.debug(message.body)
    sqs_json = message.body
    sqs = json.loads(sqs_json)
    if 'Records' not in sqs:
        return True
    for record in sqs['Records']:
        if not record['eventSource'] == "aws:s3":
            continue
        system_metadata_fields = {}
        system_metadata_fields['awsRegion'] = record['awsRegion']
        s3 = record['s3']
        system_metadata_fields['bucket_name'] = s3['bucket']['name']
        system_metadata_fields['principalId'] = \
            s3["bucket"]["ownerIdentity"]["principalId"]
        system_metadata_fields['event_type'] = record["eventName"]
        obj = s3['object']
        data_object = {
          "id": obj['key'],
          "file_size": obj['size'],
          # The time, in ISO-8601,when S3 finished processing the request,
          "created": record['eventTime'],
          "updated": record['eventTime'],
          # TODO multipart ...
          # https://forums.aws.amazon.com/thread.jspa?messageID=203436&#203436
          "checksum": obj['eTag'],
          # http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro
          "urls": ["s3://{}.s3-{}.amazonaws.com/{}".format(
                    system_metadata_fields['bucket_name'],
                    record['awsRegion'],
                    obj['key']
                    )],
          "system_metadata_fields": system_metadata_fields
        }
        logger.debug(json.dumps(data_object))
        to_kafka(args, data_object)
    return True


def consume(args):
    # Get the service resource
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
    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='s3-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')

    argparser.add_argument('--sqs_queue_name', '-qn',
                           help='''sqs queue name''',
                           default='dos-testing')

if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(
        description='Consume events from aws s3, populate kafka')
    populate_args(argparser)
    args = argparser.parse_args()
    consume(args)

