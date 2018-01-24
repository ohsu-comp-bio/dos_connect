
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
see [here](dos_connect/dos_connect/server/README.md)
