
import logging
import sys
import json
import os
from dateutil.parser import parse
from importlib import import_module

# customize for your needs
from log_setup import init_logging
from utils import AttributeDict, now, add_created_timestamps, \
                  add_updated_timestamps

# from authorizer import authorization_check
authorizer_name = os.getenv('AUTHORIZER', 'dos_connect.server.noop_authorizer')
authorizer = import_module(authorizer_name)
authorization_check = getattr(authorizer, 'authorization_check')

# from backend import save, update, delete, search
backend_name = os.getenv('BACKEND', 'dos_connect.server.memory_backend')
backend = import_module(backend_name)
save = getattr(backend, 'save')
update = getattr(backend, 'update')
delete = getattr(backend, 'delete')
search = getattr(backend, 'search')
metrics = getattr(backend, 'metrics')

# from replicator import replicate
replicator_name = os.getenv('REPLICATOR', 'dos_connect.server.noop_replicator')
replicator = import_module(replicator_name)
replicate = getattr(replicator, 'replicate')


DEFAULT_PAGE_SIZE = 100

init_logging()
log = logging.getLogger(__name__)
log.info('using authorizer {} to change set AUTHORIZER envvar'
         .format(authorizer_name))
log.info('using backend {} to change set BACKEND envvar'
         .format(backend_name))


# Data Object Controllers

@authorization_check
def CreateDataObject(**kwargs):
    """
    update timestamps, ensure version, persist
    """
    body = AttributeDict(kwargs['body']['data_object'])
    doc = add_created_timestamps(body)
    doc.current = True
    try:
        doc = save(doc, 'data_objects')
    except Exception as e:
        log.exception(e)
        return({'msg': e.message, 'status_code': 400}, 400)
    replicate(doc, 'CREATE')
    return({"data_object_id": doc.id}, 200)


@authorization_check
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
    return({'msg': "The requested Data "
                   "Object wasn't found", 'status_code': 404}, 404)


@authorization_check
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
    return({'msg': "The requested Data "
                   "Object wasn't found", 'status_code': 404}, 404)


@authorization_check
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
        replicate(data_object, 'UPDATE')
        return({"data_object_id": properties.id}, 200)
    except Exception as e:
        log.exception(e)
    return({'msg': "The requested Data "
                   "Object wasn't found", 'status_code': 404}, 404)


@authorization_check
def DeleteDataObject(**kwargs):
    """
    delete by id (all versions)
    """
    properties = AttributeDict({'id': kwargs['data_object_id']})
    delete(properties)
    replicate(properties, 'DELETE')
    return({"data_object_id": properties.id}, 200)


@authorization_check
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

@authorization_check
def CreateDataBundle(**kwargs):
    """
    update timestamps, ensure version, persist
    """
    body = AttributeDict(kwargs['body']['data_bundle'])
    doc = add_created_timestamps(body)
    doc.current = True
    try:
        doc = save(doc, 'data_bundles')
    except Exception as e:
        log.exception(e)
        return({"data_object_id": doc.id}, 409)
    replicate(doc, 'CREATE')
    return({"data_bundle_id": doc.id}, 200)


@authorization_check
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
    return({'msg': "The requested Data "
                   "Object wasn't found", 'status_code': 404}, 404)


@authorization_check
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
        # update old unset current
        update(_id=old_data_bundle.meta.id, index='data_bundles',
               doc={'current': False})
        # new is current
        data_bundle.current = True
        data_bundle.id = old_data_bundle.id
        save(data_bundle, 'data_bundles')
        replicate(data_bundle, 'UPDATE')
        return({"data_bundle_id": properties.id}, 200)
    except Exception as e:
        log.exception(e)
    return({'msg': "The requested Data "
                   "Object wasn't found", 'status_code': 404}, 404)


@authorization_check
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
    return({'msg': "The requested Data "
                   "Object wasn't found", 'status_code': 404}, 404)


@authorization_check
def DeleteDataBundle(**kwargs):
    """
    delete by id (all versions)
    """
    properties = AttributeDict({'id': kwargs['data_bundle_id']})
    delete(properties, 'data_bundles')
    replicate(properties, 'DELETE')
    return(kwargs, 200)


@authorization_check
def ListDataBundles(**kwargs):
    """
    search by keys
    """
    body = kwargs.get('body')
    property_names = ['url', 'checksum', 'alias']
    properties = AttributeDict({})
    for property_name in property_names:
        if body.get(property_name, None):
            properties[property_name] = body.get(property_name, None)
    page_size = int(body.get('page_size', DEFAULT_PAGE_SIZE))
    data_objects = [x.to_dict() for x in search(properties, 'data_bundles',
                                                size=page_size)]
    return({"data_bundles": data_objects}, 200)
