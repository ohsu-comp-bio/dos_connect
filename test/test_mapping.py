from dos_connect.observers import sqs_observer, pubsub_observer, \
    file_observer, azure_observer
from dos_connect.inventory import s3_inventory, gs_inventory, azure_inventory

from dos_connect.client import client
from watchdog.events import FileCreatedEvent
import os
import datetime
from dateutil.tz import tzutc
import json

models = client.models
DataObject = models.get_model('ga4ghDataObject')


def test_sqs_observer_to_dos():
    """ validate that a message from aws is mapped to DOS"""
    message = {
      "Records": [
        {
          "eventVersion": "2.0",
          "eventSource": "aws:s3",
          "awsRegion": "us-east-1",
          "eventTime": "1970-01-01T00:00:00.000Z",
          "eventName": "ObjectCreated:Put",
          "userIdentity": {
            "principalId": "AIDAJDPLRKLG7UEXAMPLE"
          },
          "requestParameters": {
            "sourceIPAddress": "127.0.0.1"
          },
          "responseElements": {
            "x-amz-request-id": "C3D13FE58DE4C810",
            "x-amz-id-2":
            "FMyUVURIY8/IgAtTv8xRjskZQpcIZ9KG4V5Wp6S7S/JRWeUWerMUE5JgHvANOjpD"
          },
          "s3": {
            "s3SchemaVersion": "1.0",
            "configurationId": "testConfigRule",
            "bucket": {
              "name": "mybucket",
              "ownerIdentity": {
                "principalId": "A3NL1KOZZKExample"
              },
              "arn": "arn:aws:s3:::mybucket"
            },
            "object": {
              "key": "HappyFace.jpg",
              "size": 1024,
              "eTag": "d41d8cd98f00b204e9800998ecf8427e",
              "versionId": "096fKKXTRTtl3on89fVO.nfljtsv6qko",
              "sequencer": "0055AED6DCD90281E5"
            }
          }
        }
      ]
    }
    do = DataObject.unmarshal(
        sqs_observer.to_dos(message['Records'][0])
    )
    assert do.id == "HappyFace.jpg"
    assert do.checksums[0]['checksum'] == 'd41d8cd98f00b204e9800998ecf8427e'
    assert do.urls[0]['system_metadata']['event_type'] == 'ObjectCreated:Put'


# https://cloud.google.com/storage/docs/json_api/v1/objects#resource-representations
def test_pubsub_observer_to_dos():
    class PubSubMessage:
        attributes = {
            'resource': 'projects/_/buckets/dos-testing/objects/testing.txt#1509217572944932',  # NOQA
            'objectId': 'testing.txt',
            'bucketId': 'dos-testing',
            'notificationConfig': 'projects/_/buckets/dos-testing/notificationConfigs/5',   # NOQA
            'payloadFormat': 'JSON_API_V1',
            'eventType': 'OBJECT_DELETE',
            'objectGeneration': '1509217572944932'
        }
        data = """{
            "kind": "storage#object",
            "id": "dos-testing/testing.txt/1509217572944932",
            "selfLink":
              "https://www.googleapis.com/storage/v1/b/dos-testing/o/testing.txt",
            "name": "testing.txt",
            "bucket": "dos-testing",
            "generation": "1509217572944932",
            "metageneration": "2",
            "contentType": "text/plain",
            "timeCreated": "2017-10-28T19:06:12.939Z",
            "updated": "2017-10-28T19:07:08.062Z",
            "storageClass": "REGIONAL",
            "timeStorageClassUpdated": "2017-10-28T19:06:12.939Z",
            "size": "873",
            "md5Hash": "blJQo/K03yZsMWugyHv5EQ==",
            "mediaLink": "https://www.googleapis.com/download/storage/v1/b/dos-testing/o/testing.txt?generation=1509217572944932&alt=media",
            "metadata": {
              "foo": "bar"
            },
            "crc32c": "DAxGUg==",
            "etag": "CKT4y8qBlNcCEAI="
           }"""  # NOQA

    do = DataObject.unmarshal(
        pubsub_observer.to_dos(PubSubMessage())
    )
    assert do.id == "dos-testing/testing.txt/1509217572944932"
    assert do.checksums[0]['checksum'] == 'blJQo/K03yZsMWugyHv5EQ=='
    assert (do.urls[0]['system_metadata']['event_type'] ==
            'ObjectRemoved:Delete')


def test_file_observer_to_dos():
    event = FileCreatedEvent(os.path.realpath(__file__))

    class Args():
        monitor_directory = 'foo'
        dry_run = True
        patterns = None
        ignore_patterns = None
        ignore_directories = None
        case_sensitive = None

    handler = file_observer.DOSHandler(Args())
    do = DataObject.unmarshal(
        handler.to_dos(event)
    )
    assert do.id == os.path.realpath(__file__)
    assert do.checksums[0]['checksum'] is not None
    assert do.urls[0]['system_metadata']['event_type'] == 'ObjectCreated:Put'


def test_azure_observer_to_dos():
    message_content = """{
      "topic": "/subscriptions/68106052-6b47-46b3-bd47-0cd668b9b500/resourceGroups/dostesting/providers/Microsoft.Storage/storageAccounts/dostesting",
      "subject": "/blobServices/default/containers/dos-testing/blobs/testing-20171031073707.txt",
      "eventType": "Microsoft.Storage.BlobCreated",
      "eventTime": "2017-10-31T14:39:20.415Z",
      "id": "23377130-001e-0019-5456-52940906bd44",
      "data": {
        "api": "PutBlob",
        "clientRequestId": "46896a98-be49-11e7-bbfa-acbc32be6b2d",
        "requestId": "23377130-001e-0019-5456-529409000000",
        "eTag": "0x8D5206D2BFA8492",
        "contentType": "text/plain",
        "contentLength": 8,
        "blobType": "BlockBlob",
        "url": "https://dostesting.blob.core.windows.net/dos-testing/testing-20171031073707.txt",
        "sequencer": "00000000000027AE00000000002C92E3",
        "storageDiagnostics": {
          "batchId": "8483f333-0ab2-4bec-a23b-90ae8f0465c3"
        }
      }
    }"""  # NOQA

    class Settings():
        content_md5 = '12345'
        content_type = 'text/plain'

    class Props():
        content_length = 8
        server_encrypted = True
        blob_type = 'BlockBlob'
        blob_tier_inferred = True
        blob_tier = 'Hot'
        append_blob_committed_block_count = None  # NOQA
        last_modified = datetime.datetime(2017, 10, 31, 20, 39, 36, tzinfo=tzutc())  # NOQA
        content_range = None
        etag = '"0x8D5209F803A286C"'
        page_blob_sequence_number = None
        content_settings = Settings()

    class Blob():
        metadata = {'foo': 'bar'}
        name = 'testing-20171031133540.txt'
        properties = Props()

    message_json = json.loads(message_content)
    do = DataObject.unmarshal(
        azure_observer.to_dos(message_json, Blob())
    )
    assert do.id == "https://dostesting.blob.core.windows.net/dos-testing/testing-20171031073707.txt"  # NOQA
    assert do.checksums[0]['checksum'] is not None
    assert do.urls[0]['system_metadata']['event_type'] == 'ObjectCreated:Put'
    assert do.mime_type == 'text/plain'


def test_s3_inventory_to_dos():
    """
    """
    a_dict = s3_inventory.to_dos(endpoint_url='http://test',
                        region='my-region',
                        bucket_name='my-bucket',
                        metadata={'foo': 'bar'},
                        record={u'LastModified':
                                  datetime.datetime(2017, 10, 23, 16, 20, 45, tzinfo=tzutc()),  # NOQA
                                  u'ETag': '"d3b3a66c7235c6b09a55a626861f5f91"',  # NOQA
                                  u'StorageClass': 'STANDARD',
                                  u'Key': 'passport photo.JPG', u'Size': 341005}  # NOQA
                        )  # NOQA
    do = DataObject.unmarshal(a_dict)
    assert do.urls[0]['url'] == 's3://test/my-bucket/passport+photo.JPG'


def test_gs_inventory_to_dos():
    class Bucket():
        location = 'foo'
    record = json.loads("""{
        "kind": "storage#object",
        "id": "dos-testing/testing.txt/1509217572944932",
        "selfLink":
          "https://www.googleapis.com/storage/v1/b/dos-testing/o/testing.txt",
        "name": "testing.txt",
        "bucket": "dos-testing",
        "generation": "1509217572944932",
        "metageneration": "2",
        "contentType": "text/plain",
        "timeCreated": "2017-10-28T19:06:12.939Z",
        "updated": "2017-10-28T19:07:08.062Z",
        "storageClass": "REGIONAL",
        "timeStorageClassUpdated": "2017-10-28T19:06:12.939Z",
        "size": "873",
        "md5Hash": "blJQo/K03yZsMWugyHv5EQ==",
        "mediaLink": "https://www.googleapis.com/download/storage/v1/b/dos-testing/o/testing.txt?generation=1509217572944932&alt=media",
        "metadata": {
          "foo": "bar"
        },
        "crc32c": "DAxGUg==",
        "etag": "CKT4y8qBlNcCEAI="
       }""")  # NOQA

    do = DataObject.unmarshal(gs_inventory.to_dos(Bucket(), record))
    assert do.urls[0]['url'] == "https://www.googleapis.com/download/storage/v1/b/dos-testing/o/testing.txt?generation=1509217572944932&alt=media"  # NOQA


def test_azure_inventory_to_dos():
    class Settings():
        content_md5 = '12345'
        content_type = 'text/plain'

    class Props():
        content_length = 8
        server_encrypted = True
        blob_type = 'BlockBlob'
        blob_tier_inferred = True
        blob_tier = 'Hot'
        append_blob_committed_block_count = None  # NOQA
        last_modified = datetime.datetime(2017, 10, 31, 20, 39, 36, tzinfo=tzutc())  # NOQA
        content_range = None
        etag = '"0x8D5209F803A286C"'
        page_blob_sequence_number = None
        content_settings = Settings()

    class Blob():
        metadata = {'foo': 'bar'}
        name = 'testing-20171031133540.txt'
        properties = Props()

    do = DataObject.unmarshal(azure_inventory.to_dos('http://foo.bar', Blob()))
    assert do.urls[0]['url'] == 'http://foo.bar'
