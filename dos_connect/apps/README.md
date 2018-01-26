
# applications
Several client side applications are included.

## inventory
Short lived commands to capture a snapshot of the object store.

Note: the following examples...

* use the default server configuration:
  `http://localhost:8080`.  Use the `--dos_server` parameter to communicate with your server

* use the default noop_authorizer. Use the `--api_key or DOS_API_KEY envvar` or `--user_pass DOS_USER_PASSWD envvar` to set your authentication requirement

### gdc ( genomic data commons)
```
python -m dos_connect.apps.inventory.gdc_inventory --dos_server http://localhost:8080
```

### azure inventory
```
# https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blob-event-overview
# https://docs.microsoft.com/en-us/azure/storage/queues/storage-python-how-to-use-queue-storage
# https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blob-event-quickstart
BLOB_STORAGE_ACCOUNT=XXXX \
 BLOB_STORAGE_ACCESS_KEY=YYYY \
   python -m dos_connect.apps.inventory.azure_inventory \
   --azure_container $AZURE_TEST_BUCKET
```

### google storage inventory
```
GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/google-auth-dos-testing.json \
  python -m dos_connect.apps.inventory.gs_inventory $GS_TEST_BUCKET
```

### s3 inventory
```
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
 AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
  python -m dos_connect.apps.inventory.s3_inventory  \
  $AWS_TEST_BUCKET
```

### file inventory
```
# note that the inventory function uses the same module as the observer
python -m dos_connect.apps.observers.file_observer \
  --inventory $MONITOR_DIRECTORY
```



## observers
Long lived commands to capture native event messages from the object store.


### azure observer
```
BLOB_STORAGE_ACCOUNT=$BLOB_STORAGE_ACCOUNT \
 BLOB_STORAGE_ACCESS_KEY=$BLOB_STORAGE_ACCESS_KEY \
   python -m dos_connect.apps.observers.azure_observer \
   --azure_queue $AZURE_QUEUE

AWS_ACCESS_KEY_ID=XXXXXX \
AWS_SECRET_ACCESS_KEY=XXXXXX \
AWS_DEFAULT_REGION=XXXX \
python -m dos_connect.apps.observers.sqs_observer \
--sqs_queue_name XXXX

```


### s3 observer
```
# queue needs to exist
# see https://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html
AWS_ACCESS_KEY_ID=XXXXXX \
AWS_SECRET_ACCESS_KEY=XXXXXX \
AWS_DEFAULT_REGION=XXXX \
python -m dos_connect.apps.observers.sqs_observer \
--sqs_queue_name XXXX

```

### google storage observer
```
# subscription needs to exist. see
# https://cloud.google.com/pubsub/docs/admin#create_a_pull_subscription
GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/google-auth-dos-testing.json \
python -m dos_connect.apps.observers.pubsub_observer   \
 --google_cloud_project $GOOGLE_CLOUD_PROJECT \
 --google_topic $GOOGLE_TOPIC \
 --google_subscription_name $GOOGLE_SUBSCRIPTION_NAME
```


### file observer
```
# note that the inventory function uses the same module as the observer
python -m dos_connect.apps.observers.file_observer $MONITOR_DIRECTORY
```

## plug in customizations

All observers and inventory tasks leverage a middleware plugin capability.
* user_metadata(): customize the collection of metadata
* before_store(): modify the data_object before persisting
* md5sum(): calculate the md5 of the file

To specify your own customizer, set the `CUSTOMIZER` environmental variable.
It in turn can specify it's own configuration variables, in this case `AWS_MD5_URL`

```
CUSTOMIZER=dos_connect.apps.aws_customizer AWS_MD5_URL=https://4n5huh8mw0.execute-api.us-west-2.amazonaws.com/api
```
