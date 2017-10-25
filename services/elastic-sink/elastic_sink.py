from kafka import KafkaConsumer
import json


class ElasticHandler(object):

    """Maintain DOS key/value in Elastic """

    def __init__(self,
                 elastic_url=None,
                 dry_run=False):
        super(ElasticHandler, self).__init__()
        self.elastic_url = elastic_url
        self.dry_run = dry_run

    def on_any_event(self, endpoint_url, region, bucket_name, record):
        try:
            self.process(endpoint_url, region, bucket_name, record)
        except Exception as e:
            logger.exception(e)

    def process(self, endpoint_url, region, bucket_name, record):
        """
        {u'LastModified':
            datetime.datetime(2017, 10, 23, 16, 20, 45, tzinfo=tzutc()),
        u'ETag': '"d3b3a66c7235c6b09a55a626861f5f91"',
        u'StorageClass': 'STANDARD',
        u'Key': 'passport photo.JPG', u'Size': 341005}
        """
        _event_type = 'ObjectCreated:Put'

        _id = record['Key']
        _id_parts = _id.split('/')
        _id_parts[-1] = urllib.quote_plus(_id_parts[-1])
        _id = '/'.join(_id_parts)

        _url = "s3://{}.s3-{}.amazonaws.com/{}".format(
                  bucket_name, region, _id)
        if endpoint_url:
            parsed = urlparse(endpoint_url)
            _url = 's3://{}/{}/{}'.format(parsed.netloc, bucket_name,  _id)
        _system_metadata_fields = {
            'StorageClass': record['StorageClass'],
            "event_type": _event_type,
            "bucket_name": bucket_name
        }
        data_object = {
          "id": _id,
          "file_size": record['Size'],
          # The time, in ISO-8601,when S3 finished processing the request,
          "created":  record['LastModified'].isoformat(),
          "updated":  record['LastModified'].isoformat(),
          # TODO multipart ...
          # https://forums.aws.amazon.com/thread.jspa?messageID=203436&#203436
          "checksum": record['ETag'],
          "urls": [_url],
          "system_metadata_fields": _system_metadata_fields
        }
        self.to_kafka(data_object)

    def to_kafka(self, payload):
        """ write dict to kafka """
        key = '{}~{}'.format(payload['system_metadata_fields']['event_type'],
                             payload['urls'][0])
        if self.dry_run:
            logger.debug(key)
            logger.debug(payload)
            return
        producer = KafkaProducer(bootstrap_servers=self.kafka_bootstrap)
        producer.send(args.kafka_topic, key=key, value=json.dumps(payload))
        producer.flush()
        logger.debug('sent to kafka: {} {}'.format(self.kafka_topic, key))


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

    argparser.add_argument('--group_id', '-e',
                           help='''kafka consumer group''',
                           default='elastic_sink')

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
                             consumer_timeout_ms=5000,
                             auto_offset_reset='earliest',
                             enable_auto_commit=False)
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        logger.debug("%s:%d:%d: payload=%s" % (message.topic,
                                               message.partition,
                                               message.offset,
                                               json.loads(message.value)))
        event_handler.on_any_event(message.key, json.loads(message.value))
