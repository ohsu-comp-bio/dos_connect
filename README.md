
## DOS events

![image](https://user-images.githubusercontent.com/47808/32019677-d39ac29a-b982-11e7-91f4-64924f6c5bd8.png)


* For more, Read [confluent Kafka Single Node](https://docs.confluent.io/current/cp-docker-images/docs/quickstart.html#getting-started-with-docker-compose
)  
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
  KAFKA_DOS_TOPIC=dos-topic
  KAFKA_TOPIC_UI_PORT=8000
  SQS_QUEUE_NAME=dos-testing
  SWIFT_PORT=8080
  AWS_TEST_BUCKET=dos-testing
  SWIFT_TEST_BUCKET=etl-development
  MONITOR_DIRECTORY=/files
  ```

  source the .env file
  ```
  $export  $(cat ~/kafka-connect/.env | xargs )
  ```

  initialize the services
  ```
  $bin/init
  ```

### testing
  * test the services
  ```
  $testing/aws-inventory
  $testing/aws-observer
  $testing/file-inventory
  $testing/file-observer
  $testing/swift-inventory
  $testing/swift-observer
  ```
  * visit <hostname>:$KAFKA_TOPIC_UI_PORT to see the results
  ![image](https://user-images.githubusercontent.com/47808/32018643-62b37840-b97f-11e7-9203-0e1c7f41a0be.png)


### clean
  to re-initialize the services
  ```
  $bin/clean
  ```
