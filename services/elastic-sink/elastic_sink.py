from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
import json
import argparse
import logging

logger = logging.getLogger('elastic_sink')


class ElasticHandler(object):

    """Maintain DOS key/value in Elastic """

    def __init__(self,
                 elastic_url=None,
                 dry_run=False):
        super(ElasticHandler, self).__init__()
        self.elastic_url = elastic_url
        self.dry_run = dry_run

    def on_any_event(self, key, value):
        try:
            self.process(key, value)
        except Exception as e:
            logger.exception(e)

    def process(self, key, value):
        """
        """
        self.to_elastic(key, value)

    def to_elastic(self, key, value):
        """ write dict to elastic"""
        if self.dry_run:
            logger.debug(key)
            logger.debug(value)
            return
        es = Elasticsearch([self.elastic_url])
        if key.startswith('ObjectRemoved'):
            logger.debug(key)
            url = key.split('~')[1]
            res = es.search(index='dos', doc_type='dos',
                            q='url:\"{}\"'.format(url))
            for doc in res['hits']['hits']:
                del_rsp = es.delete(index='dos', doc_type='dos', id=doc['_id'])
                logger.debug(del_rsp)
        else:
            es.create(index='dos', doc_type='dos',
                      id=value['checksum'], body=value)
            logger.debug(value)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        description='Consume events from topic, populate elastic')

    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='dos-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')

    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')

    argparser.add_argument('--elastic_url', '-e',
                           help='''elasticsearch endpoint''',
                           default='localhost:9200')

    argparser.add_argument('--group_id', '-g',
                           help='''kafka consumer group''',
                           default='elastic_sink')

    argparser.add_argument('--enable_auto_commit', '-ac',
                           help='''commit offsets ''',
                           default=False,
                           action='store_true')

    args = argparser.parse_args()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    logger.debug(args)

    event_handler = ElasticHandler(
        elastic_url=args.elastic_url,
        dry_run=args.dry_run,
    )

    # To consume latest messages and auto-commit offsets
    consumer = KafkaConsumer(args.kafka_topic,
                             group_id=args.group_id,
                             bootstrap_servers=[args.kafka_bootstrap],
                             # consumer_timeout_ms=10000,
                             auto_offset_reset='earliest',
                             enable_auto_commit=args.enable_auto_commit)
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        logger.debug("%s:%d:%d: payload=%s" % (message.topic,
                                               message.partition,
                                               message.offset,
                                               json.loads(message.value)))
        event_handler.on_any_event(message.key, json.loads(message.value))

