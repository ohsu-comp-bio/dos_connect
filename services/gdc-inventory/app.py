# Simple server implementation

import connexion
from flask_cors import CORS

import uuid
import datetime
from dateutil.parser import parse
from elasticsearch import Elasticsearch
import elasticsearch
import os 

DEFAULT_PAGE_SIZE = 100

# Our in memory registry
data_objects = {}
data_bundles = {}

_es = Elasticsearch( [os.environ['ELASTIC_URL']])
ES_INDEX = 'dos-web-app'
ES_VERSIONS = 'dos-web-app-versions'
# Application logic


def now():
    return str(datetime.datetime.now().isoformat("T") + "Z")


def get_most_recent(data_object_id):
    """ get the doc from the current index """
    doc = _es.get(index=ES_INDEX, doc_type='dos', id=data_object_id)
    return doc['_source']


def create_version(data_object_id):
    """ look up current version and back it up in ES_VERSIONS"""
    # Check to make sure we are updating an existing document.
    old_do = get_most_recent(data_object_id)
    # create history
    _es.create(index=ES_VERSIONS,
               doc_type='dos',
               id='{}-{}'.format(old_do['id'],
                                 now()),
               body=old_do)
    return old_do


def filter_data_objects(predicate):
    """
    Filters data objects according to a function that acts on each item
    returning either True or False per item.
    """
    return [
        get_most_recent(x[0]) for x in filter(predicate, data_objects.items())]


def add_created_timestamps(doc):
    """
    Adds created and updated timestamps to the document.
    """
    if 'created' not in doc:
        doc['created'] = now()
    if 'updated' not in doc:
        doc['updated'] = now()
    return doc


def add_updated_timestamps(doc):
    """
    Adds created and updated timestamps to the document.
    """
    if 'updated' not in doc:
        doc['updated'] = now()
    return doc


# Data Object Controllers


def CreateDataObject(**kwargs):
    body = kwargs['body']['data_object']
    doc = add_created_timestamps(body)
    version = doc.get('version', None)
    if not version:
        doc['version'] = now()
    if not doc.get('id', None):
        doc['id'] = doc['checksums'][0]['checksum']
    try:
        _es.create(index=ES_INDEX, doc_type='dos', id=doc['id'], body=doc)
        return({"data_object_id": doc['id']}, 200)
    except elasticsearch.exceptions.ConflictError as e:
        existing_doc = _es.get(index=ES_INDEX, doc_type='dos', id=doc['id'])
        existing_doc = existing_doc['_source']
        # same checksum, update it in place
        if not existing_doc['checksums'][0]['checksum'] == \
                doc['checksums'][0]['checksum']:
            # otherwise raise error
            raise e
        existing_urls = existing_doc['urls']
        new_urls = doc['urls']
        # first create version
        create_version(doc['id'])
        _es.update(index=ES_INDEX, doc_type='dos',
                   id=doc['checksums'][0]['checksum'],
                   body={
                    'doc': {
                        'urls': existing_urls + new_urls,
                        }
                   })
        return({"data_object_id": doc['id']}, 200)


def GetDataObject(**kwargs):
    """ get a single item """
    data_object_id = kwargs['data_object_id']
    # TODO - if current version is not one requested, look at version index
    # version = kwargs.get('version', None)
    try:
        return({"data_object": get_most_recent(data_object_id)}, 200)
    except elasticsearch.exceptions.NotFoundError as e:
        return("No Content", 404)


def GetDataObjectVersions(**kwargs):
    data_object_id = kwargs['data_object_id']
    # Get the Data Object from our dictionary
    res = es.search(index='{},{}'.format(ES_INDEX, ES_VERSIONS),
                    doc_type='dos',
                    body={
                        "query": {
                            "regexp": {
                                "id": "{}[-]*.*".format(data_object_id)
                            }
                        }
                    }
                    )
    if data_object_versions:
        return({"data_objects": data_object_versions}, 200)
    else:
        return("No Content", 404)


def UpdateDataObject(**kwargs):
    data_object_id = kwargs['data_object_id']
    body = kwargs['body']['data_object']
    try:
        create_version(data_object_id)
        # Upsert the new body in place of the old document
        doc = add_updated_timestamps(body)
        doc['created'] = old_data_object['created']
        # Set the version number to be the length of the array +1, since
        # we're about to append.
        # We need to safely set the version if they provided one that
        # collides we'll pad it. If they provided a good one, we will
        # accept it. If they don't provide one, we'll give one.
        new_version = doc.get('version', None)
        if new_version and new_version != doc['version']:
            doc['version'] = new_version
        else:
            doc['version'] = now()
        # index new doc
        _es.index(index=ES_INDEX, doc_type='dos',
                  id=data_object_id,
                  body={
                    'doc': doc
                  })
        return({"data_object_id": data_object_id}, 200)
    except elasticsearch.exceptions.NotFoundError as e:
        return("No Content", 404)


def DeleteDataObject(**kwargs):
    data_object_id = kwargs['data_object_id']
    create_version(data_object_id)
    _es.delete(index=ES_INDEX, doc_type='dos', id=data_object_id)
    return({"data_object_id": data_object_id}, 200)


def ListDataObjects(**kwargs):
    body = kwargs.get('body')


    # "alias": {
    #   "type": "string",
    #   "description": "OPTIONAL\nIf provided will only return Data Objects with the given alias."
    # },
    # "url": {
    #   "type": "string",
    #   "description": "OPTIONAL\nIf provided will return only Data Objects with a that URL matches\nthis string."
    # },
    # "checksum": {
    #   "$ref": "#/definitions/ga4ghChecksumRequest",
    #   "title": "OPTIONAL\nIf provided will only return data object messages with the provided\nchecksum. If the checksum type is provided"
    # },
    clauses = []
    for key in ['alias', 'url', 'checksum']:
        if key in body:
            clauses.append('urls.url:\"{}\"'.format(body[key]))
    q = ' AND '.join(clauses)
    res = _es.search(index='dos', doc_type='dos', q=q)
    print q
    print res
    return({"data_objects": [res['hits']['hits'][0]['_source']]}, 200)


# Data Bundle Controllers


def CreateDataBundle(**kwargs):
    temp_id = str(uuid.uuid4())
    data_bundles[temp_id] = kwargs
    return({"data_bundle_id": temp_id}, 200)


def GetDataBundle(**kwargs):
    data_bundle_id = kwargs['data_bundle_id']
    data_bundle = data_bundles[data_bundle_id]
    return({"data_bundle": data_bundle}, 200)


def UpdateDataBundle(**kwargs):
    # TODO
    # data_bundle_id = kwargs['data_bundle_id']
    # data_bundle = data_bundles[data_bundle_id]
    return(kwargs, 200)


def DeleteDataBundle(**kwargs):
    # TODO
    data_bundle_id = kwargs['data_bundle_id']
    del data_bundles[data_bundle_id]
    return(kwargs, 204)


def ListDataBundles(**kwargs):
    return(kwargs, 200)


def configure_app():
    # The model name has to match what is in
    # tools/prepare_swagger.sh controller.
    app = connexion.App(
        "app",
        specification_dir='.',
        swagger_ui=True,
        swagger_json=True)

    app.add_api('data_objects_service.swagger.json')

    CORS(app.app)
    return app


if __name__ == '__main__':
    app = configure_app()
    app.run(port=5555, debug=True)
