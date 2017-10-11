echo "## checking S3SourceConnector worker..."
curl --silent  localhost:28082/connector-plugins | grep org.apache.kafka.connect.directory.S3DirectorySourceConnector > /dev/null
if [ $? -eq 0 ]; then
  echo "S3DirectorySourceConnector found OK"
else
  echo "S3DirectorySourceConnector not found FAIL"
  echo "build connector jar via $docker run --rm -v $(pwd)/volumes/jars:/jars -it kafka-connector-builder bash"
  exit 1
fi


echo "## checking S3SourceConnector topic..."
# create it if not exists
docker run \
  --net=host \
  --rm \
  confluentinc/cp-kafka:3.3.0 \
  kafka-topics --create --topic s3-topic --partitions 1 --replication-factor 1 --if-not-exists --zookeeper localhost:32181 > /dev/null

docker run    --net=host    --rm    confluentinc/cp-kafka:3.3.0    kafka-topics --describe --zookeeper localhost:32181 | grep s3-topic > /dev/null
if [ $? -eq 0 ]; then
  echo "S3DirectorySourceConnector topic found OK"
else
  echo "S3DirectorySourceConnector topic  not found, FAIL"
  exit 1
fi


echo "## checking s3-source worker in kafka worker config..."
curl --silent --fail  localhost:28082/connectors/s3-source/status  > /dev/null
if [ $? -eq 0 ]; then
  echo "s3-source found OK"
else
  echo "### s3-source not found creating it..."
  echo "### will publish directory entries of /tmp on topic 's3-topic'..."
curl -s -X POST \
-H "Content-Type: application/json" \
--data '{ "name": "s3-source", 
 "config": {"tasks.max": 1, 
 "connector.class": "org.apache.kafka.connect.directory.S3DirectorySourceConnector", 
 "topic": "s3-topic", 
 "consumer.max.poll.records": 1000, 
 "task.shutdown.graceful.timeout.ms":30000, 
 "bucket": "etl-development", 
 "interval_ms": "60000", 
 "region_name": "us-west-2", 
 "bucket_names": "etl-development", 
 "schema_name": "s3",  
 "service_endpoint": "http://10.96.11.20:8080", 
 "key.converter": "org.apache.kafka.connect.storage.StringConverter",
 "value.converter": "org.apache.kafka.connect.storage.StringConverter",
 "internal.key.converter": "org.apache.kafka.connect.json.JsonConverter",
 "internal.value.converter": "org.apache.kafka.connect.json.JsonConverter",
 "internal.key.converter.schemas.enable": false,
 "internal.value.converter.schemas.enable": false
   } }' \
http://localhost:28082/connectors > /dev/null
  sleep 5
  curl --fail --silent  localhost:28082/connectors/s3-source/status  > /dev/null
  if [ $? -eq 0 ]; then
    echo "s3-source found OK"
  else
    echo "s3-source could not be created FAIL"
    exit 1
  fi
fi

exit 0 

echo "## read from s3-source's topic"
docker run \
 --net=host \
 --rm \
 confluentinc/cp-kafka:3.3.0 \
 kafka-console-consumer --bootstrap-server localhost:29092 --topic s3-topic --new-consumer --from-beginning --max-messages 4



docker run \
 --net=host \
 --rm \
 confluentinc/cp-kafka:3.3.0 \
 kafka-console-consumer --bootstrap-server localhost:29092 --topic s3-topic --new-consumer --from-beginning --max-messages 4 \
 --formatter kafka.tools.DefaultMessageFormatter \
      --property print.key=true \
      --property key.deserializer=org.apache.kafka.common.serialization.StringDeserializer \
      --property value.deserializer=org.apache.kafka.common.serialization.StringDeserializer




