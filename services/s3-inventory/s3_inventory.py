#!/usr/bin/env python
import os
import sys
import json
import boto3
import logging
import argparse


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

    def on_any_event(self, event):
        try:
            self.process(event)
        except Exception as e:
            logger.exception(e)

    def process(self, event):

        event_methods = {
            'deleted': 'ObjectRemoved:Delete',
            'moved': 'ObjectCreated:Copy',
            'created': 'ObjectCreated:Put',
            'modified': 'ObjectCreated:Put'
        }
        _id = event.src_path

        event.src_path.lstrip(self.monitor_directory)
        data_object = {
          "id": _id,
          "urls": [self.path2url(event.src_path)],
          "system_metadata_fields": {"event_type":
                                     event_methods.get(event.event_type),
                                     "bucket_name": self.monitor_directory}
        }

        if not event.event_type == 'deleted':
            f = os.stat(event.src_path)
            if not S_ISREG(f.st_mode):
                return
            data_object = {
              "id": _id,
              "file_size": f.st_size,
              # The time, in ISO-8601,when S3 finished processing the request,
              "created":  datetime.datetime.fromtimestamp(f.st_ctime).isoformat(),
              "updated":  datetime.datetime.fromtimestamp(f.st_mtime).isoformat(),
              # TODO multipart ...
              # https://forums.aws.amazon.com/thread.jspa?messageID=203436&#203436
              "checksum": self.md5sum(event.src_path),
              "urls": [self.path2url(event.src_path)],
              "system_metadata_fields": {"event_type":
                                         event_methods.get(event.event_type),
                                         "bucket_name": self.monitor_directory}
            }
        self.to_kafka(data_object)

    def md5sum(self, filename, blocksize=65536):
        hash = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                hash.update(block)
        return hash.hexdigest()

    def path2url(self, path):
        return urlparse.urljoin(
          'file://{}'.format(socket.gethostname()),
          urllib.pathname2url(os.path.abspath(path)))

    def to_kafka(self, payload):
        """ write dict to kafka """
        if self.dry_run:
            logger.debug(payload)
            return
        producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap)
        key = '{}~{}~{}'.format(payload['system_metadata_fields']['event_type'],
                                payload['system_metadata_fields']['bucket_name'],
                                payload.get('id', None))
        producer.send(args.kafka_topic, key=key, value=json.dumps(payload))
        producer.flush()
        logger.debug('sent to kafka: {} {}'.format(self.kafka_topic, key))


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')

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

    s3 = boto3.client('s3')
    # bucket = s3.Bucket(args.bucket_name)
    # for obj in bucket.get_all_keys():
    #     print(obj.key)
    response = s3.list_objects_v2(Bucket=args.bucket_name)
    for content in response['Contents']:
        logger.debug(content)
