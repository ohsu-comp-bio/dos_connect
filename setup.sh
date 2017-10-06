#!/bin/bash

# you should have docker & docker compose already setup
docker-compose --version >> /dev/null
if [ $? -ne 0 ]; then
  echo "you should have docker & docker compose already setup FAIL"; exit 1
fi


# initialize our host volumes
mkdir -p volumes/jars
mkdir -p volumes/elastic/backups

# create an image to build kafka connectors
echo "## checking for connector build image..."
[ ! -z $(docker images -q kafka-connector-builder:latest) ] || docker build -t kafka-connector-builder -f kafka-connector-builder.dockerfile .
if [ -z $(docker images -q kafka-connector-builder:latest) ]; then
  echo $?
  echo "builder does not exist FAIL"; exit 1
fi

echo "builder does exists OK"

# the build step already built the connector we want to use
# so copy that target to our volume
docker run --rm -v $(pwd)/volumes/jars:/jars -it kafka-connector-builder cp target/connect-directory-source-1.0-jar-with-dependencies.jar /jars

# check all ok

echo "## checking for successful build of our connector DirectorySourceConnector..."
if [ -e "volumes/jars/connect-directory-source-1.0-jar-with-dependencies.jar" ]; then
  echo "connect-directory-source-1.0-jar-with-dependencies.jar OK"
else
  echo "connect-directory-source-1.0-jar-with-dependencies.jar FAIL"
  exit 1
fi

echo "## create docker compose images..."
docker-compose create 
echo "## start docker compose images..."
docker-compose start

echo "## wait for kafka connect to start up..."
until $(curl --output /dev/null --silent  --fail localhost:28082/connectors); do
    printf '.'
    sleep 5
done
echo "kafka connect up OK"


echo "## checking DirectorySourceConnector worker..."
curl --silent  localhost:28082/connector-plugins | grep DirectorySourceConnector > /dev/null
if [ $? -eq 0 ]; then
  echo "DirectorySourceConnector found OK"
else
  echo "DirectorySourceConnector not found FAIL"
  exit 1
fi


echo "## checking DirectorySourceConnector topic..."
# create it if not exists
docker run \
  --net=host \
  --rm \
  confluentinc/cp-kafka:3.3.0 \
  kafka-topics --create --topic directory_topic --partitions 1 --replication-factor 1 --if-not-exists --zookeeper localhost:32181 > /dev/null

docker run    --net=host    --rm    confluentinc/cp-kafka:3.3.0    kafka-topics --describe --zookeeper localhost:32181 | grep directory_topic > /dev/null
if [ $? -eq 0 ]; then
  echo "DirectorySourceConnector topic found OK"
else
  echo "DirectorySourceConnector topic  not found, FAIL"
  exit 1
fi

echo "## checking directory-source worker in kafka worker config..."
curl --silent --fail  localhost:28082/connectors/directory-source/status  > /dev/null
if [ $? -eq 0 ]; then
  echo "directory-source found OK"
else
  echo "### directory-source not found creating it..."
  echo "### will publish directory entries of /tmp on topic 'directory_topic'..."
  curl -s -X POST \
  -H "Content-Type: application/json" \
  --data '{ "name": "directory-source", "config": {"tasks.max": 1, "connector.class": "org.apache.kafka.connect.directory.DirectorySourceConnector", "topic": "directory_topic", "schema.name": "directory",  "check.dir.ms": 1000, "directories.paths": "/tmp"} }' \
  http://localhost:28082/connectors > /dev/null
  sleep 5
  curl --fail --silent  localhost:28082/connectors/directory-source/status  > /dev/null
  if [ $? -eq 0 ]; then
    echo "directory-source found OK"
  else 
    echo "directory-source could not be created FAIL"
    exit 1
  fi
fi

echo "## read from directory-source's topic"
docker run \
 --net=host \
 --rm \
 confluentinc/cp-kafka:3.3.0 \
 kafka-console-consumer --bootstrap-server localhost:29092 --topic directory_topic --new-consumer --from-beginning --max-messages 10


echo "## checking elasticsearch-sink worker in kafka worker config..."
curl --silent --fail  localhost:28082/connectors/elasticsearch-sink/status  > /dev/null
if [ $? -eq 0 ]; then
  echo "elasticsearch-sink found OK"
else
  echo "### elasticsearch-sink not found creating it..."
  echo "### will read directory entries of from topic 'directory_topic' and write to elastic index 'directory_topic' ..."
  curl -X POST -H "Content-Type: application/json" --data '{"name":"elasticsearch-sink","config":{"connector.class":"io.confluent.connect.elasticsearch.ElasticsearchSinkConnector","type.name":"directory","tasks.max":"1","topics":"directory_topic","key.ignore":"true","schema.ignore":"true","connection.url":"http://localhost:9200"}}'  http://localhost:28082/connectors
  http://localhost:28082/connectors 
  sleep 5
  curl --fail --silent  localhost:28082/connectors/elasticsearch-sink/status  
  if [ $? -eq 0 ]; then
    echo "elasticsearch-sink found OK"
  else
    echo "elasticsearch-sink could not be created FAIL"
    exit 1
  fi
fi

echo '## list directory elements from elasticsearch...'
curl --silent  localhost:9200/directory_topic/_search | jq -r  .hits.hits[]._source.path | uniq
