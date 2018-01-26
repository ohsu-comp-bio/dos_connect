


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



### install

```
pip install -r requirements.txt --process-dependency-links -I
```

### setup
see [here](dos_connect/server/README.md)

