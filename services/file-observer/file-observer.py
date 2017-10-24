#!/usr/bin/env python
import os
import sys
from string import Template
from watchdog.events import PatternMatchingEventHandler, FileCreatedEvent
from watchdog.events import DirCreatedEvent
from watchdog.observers import Observer
import hashlib
import datetime
import urlparse
import urllib
import socket
from kafka import KafkaProducer
import logging
import time
import argparse
from stat import *


logger = logging.getLogger('file_observer')


class KafkaHandler(PatternMatchingEventHandler):

    """Creates DOS object on kafka queue in response to matched events."""

    def __init__(self, patterns=None, ignore_patterns=None,
                 ignore_directories=False, case_sensitive=False,
                 kafka_topic=None, kafka_bootstrap=None):
        super(KafkaHandler, self).__init__(patterns,
                                           ignore_patterns,
                                           ignore_directories,
                                           case_sensitive)
        self.kafka_topic = kafka_topic
        self.kafka_bootstrap = kafka_bootstrap
        logger.debug(
            'patterns:{} kafka_topic:{} kafka_bootstrap:{}'
            .format(patterns, kafka_topic, kafka_bootstrap))

    def on_any_event(self, event):
        try:
            logger.debug(event)
            self.process(event)
        except Exception as e:
            logger.exception(e)

    def process(self, event):
        if (event.is_directory):
            return

        f = os.stat(event.src_path)

        if not S_ISREG(f.st_mode):
            return

        event_methods = {
            'deleted': 'ObjectRemoved:Delete',
            'moved': 'ObjectCreated:Copy',
            'created': 'ObjectCreated:Put',
            'modified': 'ObjectCreated:Put'
        }

        data_object = {
          "id": event.src_path,
          "file_size": f.st_size,
          # The time, in ISO-8601,when S3 finished processing the request,
          "created":  datetime.datetime.fromtimestamp(f.st_ctime).isoformat(),
          "updated":  datetime.datetime.fromtimestamp(f.st_mtime).isoformat(),
          # TODO multipart ...
          # https://forums.aws.amazon.com/thread.jspa?messageID=203436&#203436
          "checksum": self.md5sum(event.src_path),
          # http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro
          "urls": [self.path2url(event.src_path)],
          "system_metadata_fields": {"event_type":
                                     event_methods.get(event.event_type),
                                     "bucket_name": os.getcwd()}
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
        producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap)
        key = '{}~{}~{}'.format(payload['system_metadata_fields']['event_type'],
                                payload['system_metadata_fields']['bucket_name'],
    			                payload.get('checksum', None))
        producer.send(args.kafka_topic, key=key, value=json.dumps(payload))
        producer.flush()
        logger.debug('sent to kafka topic: {}'.format(self.kafka_topic))


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')

    argparser = argparse.ArgumentParser(
        description='Consume events from directory, populate kafka')

    argparser.add_argument('--patterns', '-p',
                           help='''patterns to trigger events''',
                           default=None)

    argparser.add_argument('--ignore_patterns', '-ip',
                           help='''patterns to ignore''',
                           default=None)

    argparser.add_argument('--ignore_directories', '-id',
                           help='''dir events''',
                           default=False)

    argparser.add_argument('--case_sensitive', '-cs',
                           help='''case_sensitive''',
                           default=False)

    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='s3-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')

    argparser.add_argument('--inventory', '-i',
                           help='''create event for existing files''',
                           default=False,
                           action='store_true')

    argparser.add_argument('monitor_directory',
                           help='''directory to monitor''',
                           default='.')

    args = argparser.parse_args()

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    path = args.monitor_directory
    event_handler = KafkaHandler(
        patterns=args.patterns,
        ignore_patterns=args.ignore_patterns,
        ignore_directories=args.ignore_directories,
        case_sensitive=args.case_sensitive,
        kafka_topic=args.kafka_topic,
        kafka_bootstrap=args.kafka_bootstrap
    )

    for root, dirs, files in os.walk(path):
        if not args.ignore_directories:
            for name in dirs:
                event_handler.on_any_event(DirCreatedEvent(
                    os.path.join(path, name)))
        for name in files:
            event_handler.on_any_event(FileCreatedEvent(
                    os.path.join(path, name)))

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
