


## DOS connect

### concept
Exercise the [GA4GH data-object-schemas]( https://github.com/ga4gh/data-object-schemas)

![image](https://user-images.githubusercontent.com/47808/32701068-36d6db5a-c784-11e7-890d-916109745027.png)


### epics

* As a researcher, in order to maximize the amount of data I can process  from disparate repositories,  I can use DOS to harmonize those repositories
* As a researcher, in order to minimize cloud costs and processing time,  I can use DOS' to harmonized data to make decisions about what platform/region I should use to download from or where my code should execute.
* As a informatician, in order to injest from disparate repositories,  I need to injest an existing repository into DOS
* As a informatician, in order to keep DOS up to date,  I need to observe changes to the repository and automatically update DOS
* As a developer, in order to enable DOS,  I need to integrate DOS into my backend stack


### capabilities

This project provides two high level capabilities:
* observation: long lived services to observe the object store and populate a kafka topic with [data-object-schema](https://github.com/ga4gh/data-object-schemas/blob/master/proto/data_objects.proto) records. These observations catch add, moves and deletes to the object store.
* inventory: on demand commands to capture a snapshot of the object store.  Inventory commands populate the same queue

For development and proof of concept, a docker-compose setup is provided.
* Kafka is used to enable multiple downstream consumer ETL
* An elastic-sink service is provided to illustrate the consuming from the topic and maintaining a user facing query store.
`Note`: there are no fixed dependencies, see customizations if you would like to use other backends.

![image](https://user-images.githubusercontent.com/47808/32701215-40c677cc-c786-11e7-994a-0423ce3d8e9a.png)



### setup

  Bucket setup (for observers, not required for inventory)
  * [azure](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blob-event-overview)
  * [google](https://cloud.google.com/storage/docs/pubsub-notifications)
  * [aws](http://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html)
  * [swift](https://github.com/redhat-cip/swift-middleware-sample)


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
  $ export  $(cat ~/kafka-connect/.env | grep -v "#" | xargs )
  ```

  initialize the services
  ```
  $bin/init
  ```
  * For more, Read [Kafka Single Node](https://github.com/Landoop/fast-data-dev )

### testing
  * unit tests
  ```
  $pytest
  ```

  * send ad-hoc test messages
  ```
  $util/aws-inventory
  $util/aws-observer
  $util/file-inventory
  $util/file-observer
  $util/swift-inventory
  $util/swift-observer
  $util/azure-observer
  $util/azure-inventory
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

### customize
  All Kafka code can be overwritten
  * dos_connect/observers/customizations.py
  * dos_connect/inventory/customizations.py  

### todo
  * refactor to move kafka & elastic behind standard webserver
  ![image](https://user-images.githubusercontent.com/47808/32866456-cc4d7438-ca1c-11e7-888a-799f2e630691.png)
