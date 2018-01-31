#!/usr/bin/python
# -*- encoding: utf-8 -*-

# customize for your replication needs

import logging
from kafka import KafkaProducer

log = logging.getLogger(__name__)


KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', None)
producer = None
if KAFKA_BOOTSTRAP_SERVERS:
    KAFKA_DOS_TOPIC = os.getenv('KAFKA_DOS_TOPIC', None)
    assert KAFKA_DOS_TOPIC
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)


# replicate implementation


def replicate(doc, method):
    '''send data downstream'''
    if producer:
        producer.send(KAFKA_DOS_TOPIC,
                      json.dumps({'method': method, 'doc': doc}))
        producer.flush()
