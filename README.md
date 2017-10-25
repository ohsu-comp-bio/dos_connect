
## Getting Started with Docker Compose

Kafka Single Node
Read confluent doc  https://docs.confluent.io/current/cp-docker-images/docs/quickstart.html#getting-started-with-docker-compose

### setup
  create .env file in the cloned repo
  ```
  AWS_ACCESS_KEY_ID=XXXXX
  AWS_SECRET_ACCESS_KEY=XXXXX
  AWS_DEFAULT_REGION=us-west-2
  SWIFT_ACCESS_KEY_ID=YYY
  SWIFT_SECRET_ACCESS_KEY=YYY
  ZOOKEEPER_CLIENT_PORT=32181
  KAFKA_ZOOKEEPER_CONNECT=localhost:32181
  KAFKA_BOOTSTRAP_SERVERS=localhost:29092
  KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://$KAFKA_BOOTSTRAP_SERVERS
  KAFKA_REST_ZOOKEEPER_CONNECT=$KAFKA_ZOOKEEPER_CONNECT
  KAFKA_REST_LISTENERS=http://localhost:8082
  KAFKA_REST_HOST_NAME=localhost
  KAFKA_DOS_TOPIC=DOS-Topic
  KAFKA_TOPIC_UI_PORT=8000
  SQS_QUEUE_NAME=dos-testing  
  ```

  source the .env file
  ```
  $export  $(cat ~/kafka-connect/.env | xargs )
  ```

  initialize the system
  ```
  $bin/init
  ```
