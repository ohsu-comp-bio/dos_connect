from kafka import KafkaConsumer
import json

# To consume latest messages and auto-commit offsets
consumer = KafkaConsumer('directory_topic',
                         group_id='my-group',
                         bootstrap_servers=['localhost:29092'],
                         consumer_timeout_ms=5000, 
			 auto_offset_reset='earliest', enable_auto_commit=False) 
for message in consumer:
    # message value and key are raw bytes -- decode if necessary!
    # e.g., for unicode: `message.value.decode('utf-8')`
    print ("%s:%d:%d: payload=%s"      % (message.topic, message.partition,
                                          message.offset, 
                                          json.loads(message.value)['payload']))
