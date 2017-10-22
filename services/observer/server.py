#!/usr/bin/env python

"""
Observe object store updates from [swift,s3]
"""

import os

from flask import Flask, request, jsonify, Response, json
from kafka import KafkaProducer
import requests
import json
import argparse
import os

app = Flask(__name__)


# @app.errorhandler(ValidationError)
# def on_validation_error(e):
#     return "error"


@app.route('/swift', methods=['GET', 'POST'])
def swift():
    app.logger.info('request.json: {}'.format(request.get_json()))
    save(request.get_json())
    return jsonify({
      "status": "OK"
    })


def save(payload):
    """ write dict to kafka """
    producer = KafkaProducer(bootstrap_servers=app.config['_kafka_bootstrap'])
    producer.send(app.config['_kafka_topic'], json.dumps(payload))
    producer.flush()
    app.logger.info('sent to kafka topic: {}'.format(app.config['_kafka_topic']))


def populate_args(argparser):
    """add arguments we expect """
    default_host="0.0.0.0"
    default_port=5000
    argparser.add_argument("-H", "--host",
                      help="Hostname of the Flask app " + \
                           "[default %s]" % default_host,
                      default=default_host)
    argparser.add_argument("-P", "--port", type=int,
                      help="Port for the Flask app " + \
                           "[default %s]" % default_port,
                      default=default_port)

    argparser.add_argument("-d", "--debug",
                      action="store_true", dest="debug", default=True)
    argparser.add_argument("-p", "--profile",
                      action="store_true", dest="profile")

    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default= os.getenv('KAFKA_TOPIC', 'swift-observer'))

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default= os.getenv('KAFKA_BOOTSTRAP', 'localhost:9092'))

#  MAIN -----------------
if __name__ == '__main__':  # pragma: no cover
    argparser = argparse.ArgumentParser(description='Observer events from swift webhook')
    populate_args(argparser)
    args = argparser.parse_args()
    app.logger.info(args)
    app.config['_kafka_topic'] = args.kafka_topic
    app.config['_kafka_bootstrap'] = args.kafka_bootstrap

    app.run(debug=args.debug, port=args.port, host=args.host)

