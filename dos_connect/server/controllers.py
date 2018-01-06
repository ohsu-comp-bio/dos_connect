import uuid
import datetime

from dateutil.parser import parse

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

import logging
import sys
import os
from decorator import decorator
import flask

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# # turn on max debugging
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter(
#             '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ch.setFormatter(formatter)
log.addHandler(ch)
# # allow printing of POST body as well.
import httplib  # noqa
httplib.HTTPConnection.debuglevel = logging.DEBUG
logging.getLogger("urllib3").setLevel(logging.DEBUG)


DEFAULT_PAGE_SIZE = 100

# connect to elastic
client = Elasticsearch()
assert client.info()
# check persistence options in env
ES_REFRESH_ON_PERSIST = os.getenv('ES_REFRESH_ON_PERSIST', 'False')
ES_REFRESH_ON_PERSIST = not (ES_REFRESH_ON_PERSIST == 'False')
if not ES_REFRESH_ON_PERSIST:
    log.info('ES_REFRESH_ON_PERSIST not set (default),'
             ' ES writes defer index refresh')
else:
    log.info('ES_REFRESH_ON_PERSIST set, ES writes will refresh index')


# allow us to use dot notation for dicts
class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


# auth implementation
def check_auth(username, password):
    '''This function is called to check if a username /
    password combination is valid.'''
    log.info('check_auth {} {}'.format(username, password))
    return username == 'admin' and password == 'secret'


def authenticate():
    '''Sends a 401 response that enables basic auth'''
    return flask.Response('You have to login with proper credentials', 401,
                          {'WWW-Authenticate': 'Basic realm="Login Required"'})


@decorator
def requires_auth(f, *args, **kwargs):
    auth = flask.request.authorization
    log.info('requires_auth {}'.format(auth))
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return f(*args, **kwargs)

# Application logic


def now():
    """
    get string iso date in zulu
    """
    return str(datetime.datetime.now().isoformat("T") + "Z")


def add_created_timestamps(doc):
    """
    Adds created and updated timestamps to the document.
    """
    doc['created'] = now()
    doc['updated'] = now()
    return doc


def add_updated_timestamps(doc):
    """
    Adds updated timestamp to the document.
    """
    doc['updated'] = now()
    return doc


def save(doc, index='data_objects'):
    """
    save the body in the index, ensure version and id set
    """
    version = doc.get('version', None)
    if not version:
        doc['version'] = now()
    if not doc.get('id', None):
        temp_id = str(uuid.uuid4())
        doc['id'] = temp_id
    # create index, use index name singular as doc type
    # do not wait for search available See
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-refresh.html
    result = client.index(index=index,
                          body=doc,
                          doc_type=index[:-1],
                          timeout='120s',
                          request_timeout=120,
                          op_type='index',
                          refresh=ES_REFRESH_ON_PERSIST
                          )
    return doc


def update(_id, doc, index='data_objects'):
    """
    partial update using the es contructed _id
    """
    log.debug(doc)
    result = client.update(index=index,
                           doc_type=index[:-1],
                           id=_id,
                           body={"doc": doc},
                           refresh=ES_REFRESH_ON_PERSIST
                           )
    log.debug(result)


def search(properties, index='data_objects', size=DEFAULT_PAGE_SIZE,
           offset=0, include_total=False):
    """
    get all objects that match
    if include_total set, return tuple (hit, total)
    """
    s = Search(using=client, index=index)
    clauses = ['*']
    for k in properties.keys():
        v = properties[k]
        # quote everything except booleans
        if not isinstance(v, bool):
            clauses.append('+{}:"{}"'.format(k, v))
        else:
            clauses.append('+{}:{}'.format(k, str(v).lower()))
    s = s.query("query_string", query=' '.join(clauses))
    s = s[offset:offset+size]
    # s = s.sort('-updated').params(preserve_order=True)
    # log.debug(s.to_dict())
    # for _, hit in enumerate(s.scan()):
    #     log.debug(hit.to_dict())
    #     yield hit
    s = s.sort('-updated')
    log.debug(s.to_dict())
    response = s.execute()
    total = response.hits.total
    for _, hit in enumerate(response):
        log.debug(hit.to_dict())
        if include_total:
            yield (hit, total)
        else:
            yield hit


def delete(properties, index='data_objects'):
    """
    delete item from index
    """
    s = Search(using=client, index=index)
    clauses = []
    for k in properties.keys():
        v = properties[k]
        clauses.append('+{}:"{}"'.format(k, v))
    s = s.query("query_string", query=' '.join(clauses))
    log.debug(s.to_dict())
    s.delete()

# Data Object Controllers


def CreateDataObject(**kwargs):
    """
    update timestamps, ensure version, persist
    """
    body = AttributeDict(kwargs['body']['data_object'])
    doc = add_created_timestamps(body)
    doc.current = True
    doc = save(doc, 'data_objects')
    return({"data_object_id": doc.id}, 200)


def GetDataObject(**kwargs):
    """
    get by id
    """
    properties = AttributeDict({'id': kwargs['data_object_id']})
    version = kwargs.get('version', None)
    if version:
        properties['version'] = version
    # Get the Data Object from our dictionary
    try:
        data_object = search(properties, size=1).next()
        if data_object:
            return({"data_object": data_object.to_dict()}, 200)
    except Exception as e:
        log.exception(e)
    return("No Content", 404)


def GetDataObjectVersions(**kwargs):
    """
    get all versions
    """
    properties = AttributeDict({'id': kwargs['data_object_id']})
    # Get the Data Object from our dictionary
    try:
        versions = [x.to_dict() for x in search(properties)]
        if versions:
            return({"data_objects": versions}, 200)
    except Exception as e:
        log.exception(e)
        return("No Content", 404)


def UpdateDataObject(**kwargs):
    """
    version dataobject
    """
    properties = AttributeDict({'id': kwargs['data_object_id']})
    body = AttributeDict(kwargs['body']['data_object'])
    try:
        old_data_object = search(properties).next()
        data_object = add_updated_timestamps(body)
        data_object.created = old_data_object.created
        # We need to safely set the version if they provided one that
        # collides we'll pad it. If they provided a good one, we will
        # accept it. If they don't provide one, we'll give one.
        new_version = data_object.get('version', None)
        if new_version and new_version != old_data_object.version:
            data_object.version = new_version
        else:
            data_object.version = now()
        data_object.id = old_data_object.id
        # update old unset current
        update(_id=old_data_object.meta.id, doc={'current': False})
        # new is current
        data_object.current = True
        save(data_object, 'data_objects')
        return({"data_object_id": properties.id}, 200)
    except Exception as e:
        log.exception(e)
        return("No Content", 404)


def DeleteDataObject(**kwargs):
    """
    delete by id (all versions)
    """
    properties = AttributeDict({'id': kwargs['data_object_id']})
    delete(properties)
    return({"data_object_id": properties.id}, 200)


def ListDataObjects(**kwargs):
    """
    search by keys
    """
    body = kwargs.get('body')
    property_names = ['url', 'checksum', 'alias']
    properties = AttributeDict({})
    for property_name in property_names:
        if body.get(property_name, None):
            properties[property_name] = body.get(property_name, None)
    #  see https://github.com/ga4gh/data-object-schemas/issues/33
    if 'alias' in properties:
        properties.aliases = properties.alias
        del properties['alias']
    if 'checksum' in properties:
        properties['checksums.checksum'] = properties.checksum['checksum']
        del properties['checksum']
    if 'url' in properties:
        properties['urls.url'] = properties.url
        del properties['url']
    properties.current = True  # only current, no previous
    page_size = int(body.get('page_size', DEFAULT_PAGE_SIZE))
    offset = int(body.get('next_page_token', 0))
    total = 0
    data_objects = [x.to_dict() for x, total in search(properties, offset=offset, size=page_size, include_total=True)]  # noqa
    response = {"data_objects": data_objects}
    if (offset + page_size) < total:
        response['next_page_token'] = str(offset + page_size)
    return(response, 200)


# Data Bundle Controllers

@requires_auth
def CreateDataBundle(**kwargs):
    """
    update timestamps, ensure version, persist
    """
    body = AttributeDict(kwargs['body']['data_bundle'])
    doc = add_created_timestamps(body)
    doc = save(doc, 'data_bundles')
    return({"data_bundle_id": doc.id}, 200)


def GetDataBundle(**kwargs):
    """
    get by id
    """
    properties = AttributeDict({'id': kwargs['data_bundle_id']})
    version = kwargs.get('version', None)
    if version:
        properties['version'] = version
    # Get the Data Object from our dictionary
    try:
        data_bundle = search(properties, 'data_bundles').next()
        if data_bundle:
            return({"data_bundle": data_bundle.to_dict()}, 200)
    except Exception as e:
        log.exception(e)
    return("No Content", 404)


def UpdateDataBundle(**kwargs):
    """
    get all versions
    """
    properties = AttributeDict({'id': kwargs['data_bundle_id']})
    body = AttributeDict(kwargs['body']['data_bundle'])
    try:
        old_data_bundle = search(properties, 'data_bundles').next()
        data_bundle = add_updated_timestamps(body)
        data_bundle.created = old_data_bundle.created
        new_version = data_bundle.get('version', None)
        if new_version and new_version != old_data_bundle.version:
            data_bundle.version = new_version
        else:
            data_bundle.version = now()
        data_bundle.id = old_data_bundle.id
        save(data_bundle, 'data_bundles')
        return({"data_bundle_id": properties.id}, 200)
    except Exception as e:
        log.exception(e)
        return("No Content", 404)


def GetDataBundleVersions(**kwargs):
    """
    version dataobject
    """
    properties = AttributeDict({'id': kwargs['data_bundle_id']})
    # Get the Data Object from our dictionary
    try:
        versions = [x.to_dict() for x in search(properties, 'data_bundles')]
        if versions:
            return({"data_bundles": versions}, 200)
    except Exception as e:
        log.exception(e)
        return("No Content", 404)


def DeleteDataBundle(**kwargs):
    """
    delete by id (all versions)
    """
    properties = AttributeDict({'id': kwargs['data_bundle_id']})
    delete(properties, 'data_bundles')
    return(kwargs, 200)


def ListDataBundles(**kwargs):
    """
    search by keys
    """
    body = kwargs.get('body')
    property_names = ['url', 'checksum', 'alias']
    properties = {}
    for property_name in property_names:
        if body.get(property_name, None):
            properties[property_name] = body.get(property_name, None)
    #  see https://github.com/ga4gh/data-object-schemas/issues/33
    if 'alias' in properties:
        properties['aliases'] = properties['alias']
        del properties['alias']
    if 'checksum' in properties:
        properties['checksums.checksum'] = properties['checksum']['checksum']
        del properties['checksum']
    if 'url' in properties:
        properties['urls.url'] = properties['url']
        del properties['url']

    page_size = int(body.get('page_size', DEFAULT_PAGE_SIZE))
    data_objects = [x.to_dict() for x in search(properties, 'data_bundles',
                                                size=page_size)]
    return({"data_bundles": data_objects}, 200)
