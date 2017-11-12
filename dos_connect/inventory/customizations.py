from kafka import KafkaProducer
import logging
import json

_PRODUCER = None


def store(args, payload):
    logger = logging.getLogger(__name__)
    """ write dict to kafka """
    key = '{}~{}'.format(payload['urls'][0]['system_metadata']['event_type'],
                         payload['urls'][0]['url'])
    if not args.dry_run:
        producer = _producer(args)
        producer.send(args.kafka_topic, key=key, value=json.dumps(payload))
        producer.flush()
        logger.info('sent to kafka topic: {} {}'
                    .format(args.kafka_topic, key))
    else:
        logger.info('dry_run to kafka topic: {} {}'
                    .format(args.kafka_topic, key))


def custom_args(argparser):
    """add arguments we expect """

    argparser.add_argument('--no_tls',
                           help='kafka connection plaintext? default: False',
                           default=False,
                           action='store_true')

    argparser.add_argument('--ssl_cafile',
                           help='server CA pem file',
                           default='/client-certs/CARoot.pem')

    argparser.add_argument('--ssl_certfile',
                           help='client certificate pem file',
                           default='/client-certs/certificate.pem')

    argparser.add_argument('--ssl_keyfile',
                           help='client private key pem file',
                           default='/client-certs/key.pem')

    argparser.add_argument('--kafka_topic', '-kt',
                           help='''kafka_topic''',
                           default='s3-topic')

    argparser.add_argument('--kafka_bootstrap', '-kb',
                           help='''kafka host:port''',
                           default='localhost:9092')


def _producer(args):
    """ create a connection """
    global _PRODUCER
    if not _PRODUCER:
        if not args.no_tls:
            _PRODUCER = KafkaProducer(bootstrap_servers=args.kafka_bootstrap,
                                      security_protocol='SSL',
                                      ssl_check_hostname=False,
                                      ssl_cafile=args.ssl_cafile,
                                      ssl_certfile=args.ssl_certfile,
                                      ssl_keyfile=args.ssl_keyfile)
        else:
            _PRODUCER = KafkaProducer(bootstrap_servers=args.kafka_bootstrap)

    return _PRODUCER
