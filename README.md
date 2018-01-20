
## DOS events

![image](https://user-images.githubusercontent.com/47808/32254182-63da596e-be5c-11e7-9a6a-4c44c720e25c.png)


This project provides two high level capabilities:
* observation: long lived services to observe the object store and populate a kafka topic with [data-object-schema](https://github.com/ga4gh/data-object-schemas/blob/master/proto/data_objects.proto) records. These observations catch add, moves and deletes to the object store.
* inventory: on demand commands to capture a snapshot of the object store.  Inventory commands populate the same queue

For development and proof of concept, a docker-compose setup is provided.
A elastic-sink service is provided to illustrate the consuming from the topic and maintaining a user facing query store.


### install

```
pip install -r requirements.txt --process-dependency-links -I
```

### setup
  create .env file in the cloned repo
  ```
  # common
  ZOOKEEPER_CLIENT_PORT=2182
  KAFKA_ZOOKEEPER_CONNECT=XX.XX.XX.XX:2182
  KAFKA_BOOTSTRAP_SERVERS=XX.XX.XX.XX:9092
  KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://XX.XX.XX.XX:9092
  KAFKA_REST_ZOOKEEPER_CONNECT=localhost:2182
  KAFKA_REST_LISTENERS=http://localhost:8082
  KAFKA_REST_HOST_NAME=localhost
  KAFKA_DOS_TOPIC=dos-topic

  # utility
  KAFKA_TOPIC_UI_PORT=8000
  ELASTIC_URL=localhost:9200

  # file system
  MONITOR_DIRECTORY=/files

  # swift
  SWIFT_ACCESS_KEY_ID=XXX
  SWIFT_SECRET_ACCESS_KEY=XXX
  SWIFT_PORT=8080
  SWIFT_TEST_BUCKET=etl-development

  # google
  PUBSUB_QUEUE_NAME=dos-testing
  GS_TEST_BUCKET=dos-testing

  # aws
  AWS_TEST_BUCKET=dos-testing
  SQS_QUEUE_NAME=dos-testing
  AWS_ACCESS_KEY_ID=XXX
  AWS_SECRET_ACCESS_KEY=XXX
  AWS_DEFAULT_REGION=us-west-2

  # azure
  QUEUE_STORAGE_ACCOUNT=dostestingq
  QUEUE_STORAGE_ACCESS_KEY=XXX
  BLOB_STORAGE_ACCOUNT=dostesting
  BLOB_STORAGE_ACCESS_KEY=XXX
  AZURE_TEST_BUCKET=dos-testing
  AZURE_QUEUE=dos-testing
  ```

  source the .env file
  ```
  export  $(cat .env | grep -v "#" | xargs )
  ```

  initialize the services
  ```
  $bin/init
  ```
  * For more, Read [confluent Kafka Single Node](https://docs.confluent.io/current/cp-docker-images/docs/quickstart.html#getting-started-with-docker-compose
  )

### testing
  * test the services
  ```
  $testing/aws-inventory
  $testing/aws-observer
  $testing/file-inventory
  $testing/file-observer
  $testing/swift-inventory
  $testing/swift-observer
  $testing/azure-observer
  $testing/azure-inventory
  ```
  * visit hostname:$KAFKA_TOPIC_UI_PORT to see the results
  ![image](https://user-images.githubusercontent.com/47808/32018643-62b37840-b97f-11e7-9203-0e1c7f41a0be.png)

  * see results in elastic
  ![image](https://user-images.githubusercontent.com/47808/32027500-3787c350-b99e-11e7-8da2-77e38509af33.png)



### clean
  to re-initialize the services
  ```
  $bin/clean
  ```

### TODO
  dos_schemas
  * security
  * add 404 response type

### testing
  # start server
 py.test --no-print-logs test/test_server.py
