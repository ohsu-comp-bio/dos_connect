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
  echo "builder does not exist FAIL"; exit 1
fi
echo "builder exists OK"

docker inspect  --format="{{.State.Running}}" builder > /dev/null
if [ $? -ne 0 ]; then
  echo "## Starting builder..."
  docker run --name builder -v $(pwd)/volumes/jars:/jars -d -t kafka-connector-builder bash
fi
docker inspect  --format="{{.State.Running}}" builder > /dev/null
if [ $? -ne 0 ]; then
  echo "builder not running FAIL"; exit 1
fi
echo "builder running OK"

# echo "## building connectors ..."
# rm -f volumes/jars/connect-directory-source-1.0-all.jar
# # the build step already built the connector we want to use
# # so copy that target to our volume
# docker exec builder bash -c "git pull origin s3; gradle shadowJar; cp build/libs/connect-directory-source-1.0-all.jar  /jars"
#
# # check all ok

echo "## checking for successful build of our connector DirectorySourceConnector..."
if [ -e "volumes/jars/connect-directory-source-1.0-all.jar" ]; then
  echo "connect-directory-source-1.0-all.jar OK"
else
  echo "connect-directory-source-1.0-all.jar FAIL"
  exit 1
fi

echo "## create docker compose images..."
DC='docker-compose -f docker-compose.yml -f docker-compose.mac.yml'
$DC create
echo "## start docker compose images..."
$DC start

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
 kafka-console-consumer --bootstrap-server localhost:29092 --topic directory_topic --new-consumer --from-beginning --max-messages 4


echo "## checking elasticsearch-sink worker in kafka worker config..."
curl --silent --fail  localhost:28082/connectors/elasticsearch-sink/status  > /dev/null
if [ $? -eq 0 ]; then
  echo "elasticsearch-sink found OK"
else
  echo "### elasticsearch-sink not found creating it..."
  echo "### will read directory entries of from topic 'directory_topic' and write to elastic index 'directory_topic' ..."
  curl --silent -X POST -H "Content-Type: application/json" --data '{"name":"elasticsearch-sink","config":{"connector.class":"io.confluent.connect.elasticsearch.ElasticsearchSinkConnector","type.name":"directory","tasks.max":"1","topics":"directory_topic","key.ignore":"true","schema.ignore":"true","connection.url":"http://localhost:9200"}}'  http://localhost:28082/connectors > /dev/null
  printf '.'
  sleep 10
  curl --fail --silent  localhost:28082/connectors/elasticsearch-sink/status  > /dev/null
  if [ $? -eq 0 ]; then
    echo "elasticsearch-sink found OK"
  else
    echo "elasticsearch-sink could not be created FAIL"
    exit 1
  fi
fi

echo "## wait for elastic index to create ..."
until $(curl --output /dev/null --silent  --fail localhost:9200/directory_topic); do
    printf '.'
    sleep 5
done
echo "elastic index created OK"

echo '## list directory elements from elasticsearch...'
curl --silent  localhost:9200/directory_topic/_search | jq -r  .hits.hits[]._source.path | sort |  uniq

# create an image to build python consumer
echo "## checking for python consumer image..."
[ ! -z $(docker images -q python-kafka-consumer:latest) ] || docker build -t python-kafka-consumer -f python-kafka-consumer.dockerfile .
if [ -z $(docker images -q python-kafka-consumer:latest) ]; then
  echo $?
  echo "python-kafka-consumer does not exist FAIL"; exit 1
fi
echo "python-kafka-consumer does exists OK"

echo "## consuming directory_topic from python 'native' client..."
docker run  --net=host --rm -it -v $(pwd)/directory_consumer.py:/directory_consumer.py python-kafka-consumer python /directory_consumer.py
if [ $? -eq 0 ]; then
  echo "directory_consumer.py OK"
else
  echo "directory_consumer.py FAIL"
  exit 1
fi

echo "## consuming directory_topic meta data from REST interface ..."
curl --silent localhost:8082/topics | grep directory_topic > /dev/null
if [ $? -eq 0 ]; then
  echo "REST metadata OK"
else
  echo "REST metadata FAIL"
  exit 1
fi


# Create a consumer for JSON data, starting at the beginning of the topic's
# log and subscribe to a topic. Then consume some data using the base URL in the first response.
# Finally, close the consumer2 with a DELETE to make it leave the group and clean up
# its resources.
echo "## setting up REST consumer..."
curl --silent  -X POST -H "Content-Type: application/vnd.kafka.v2+json" \
      --data '{"name": "my_consumer_instance", "format": "json", "auto.offset.reset": "earliest"}' \
      http://localhost:8082/consumers/my_json_consumer > /dev/null

echo "## setting up REST consumer subscription to directory_topic..."
curl --silent -X POST -H "Content-Type: application/vnd.kafka.v2+json" --data '{"topics":["directory_topic"]}' \
 http://localhost:8082/consumers/my_json_consumer/instances/my_consumer_instance/subscription
 # No content in response


echo "## get REST consumer directory_topic messages..."
while :
do
  curl --silent -X GET -H "Accept: application/vnd.kafka.json.v2+json" http://localhost:8082/consumers/my_json_consumer/instances/my_consumer_instance/records | grep directory_topic
  if [ $? -eq 0 ]
  then
  	break            #Abandon the loop.
  fi
  printf '.'
  sleep 5
done


echo "## delete REST consumer..."
curl -X DELETE -H "Content-Type: application/vnd.kafka.v2+json" \
       http://localhost:8082/consumers/my_json_consumer/instances/my_consumer_instance
  # No content in response
