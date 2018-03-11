#!/usr/bin/env python

import os
import json
from pprint import pprint
import inspect
import sys
import argparse

import sevenbridges as sbg
from sevenbridges.models.file import File

from ga4gh.dos.client import Client

from .. import common_args, common_logging,  client_factory, custom_args


class CavatacaGenerator():
    def __init__(self, project_id, token, url):
        self.api = sbg.Api(url=url, token=token)
        self.project_id = project_id

    def project(self):
        ''' return cavataca project '''
        return self.api.projects.get(id=self.project_id)

    def tasks(self):
        ''' generator cavataca project.tasks '''
        for t in self.api.tasks.query(project=self.project_id).all():
            yield t

    def output_files(self, task):
        ''' generator cavataca project.task.outputs()
            returns tuple (output_file, output_key )'''
        def _is_file(item):
            if isinstance(item, sbg.models.file.File):
                return True
            if isinstance(item, dict):
                return item.get('class', None) == 'File'
            return False

        def _to_file(item):
            # print self._files_by_origin.get(item['path'], None)
            return self._files_by_origin.get(item['path'], item)

        for output_key in getattr(task, 'outputs', None) or []:
            # print '    output_name:{}'.format(output_name)
            output_value = task.outputs.get(output_key)
            if isinstance(output_value, list):
                # print '      is list'
                for item in output_value:
                    # print '      item:{} {}'.format(item.__class__, item)
                    if _is_file(item):
                        yield _to_file(item), output_key
            else:
                # print '      output_value:{} {}'.format(output_value.__class__, output_value)  # NOQA
                if _is_file(output_value):
                    yield _to_file(output_value), output_key

    def all_output_files(self):
        ''' generator cavataca project.task.outputs()
            returns tuple (output_value, output_key, task, project )'''
        for task in self.tasks():
            # print '  task:{}'.format(task.id)
            for (output_file, output_key) in self.output_files(task=task):
                yield output_file, output_key, task, self.project

    def all_task_files(self):
        ''' generator cavataca project.task.outputs()
            returns tuple (output_value, output_key, task, project )'''
        for task in self.tasks():
            print 'task:{}'.format(task.id)
            for output_file in self._files_by_origin.get(task.id, []):
                yield output_file, task, self.project

    def files(self):
        ''' generator cavataca project.files() '''
        for f in self.api.files.query(project=self.project_id):
            yield f


def cavataca_to_ga4gh(file_):
    """
    Accepts a file_tuple and returns a DataObjectRequest
    :return:
    """
    DataObject = models.get_model('ga4ghDataObject')
    URL = models.get_model('ga4ghURL')
    Checksum = models.get_model('ga4ghChecksum')
    # pprint(file_._data.data)
    # {u'created_on': u'2018-03-03T00:00:59Z',
    #  u'href': u'https://cavatica-api.sbgenomics.com/v2/files/5a99e5bb4f0c9ab63d0ae8c9',
    #  u'id': u'5a99e5bb4f0c9ab63d0ae8c9',
    #  u'metadata': {},
    #  u'modified_on': u'2018-03-03T00:00:59Z',
    #  u'name': u'1000G_omni2.5.hg38.vcf.gz',
    #  u'origin': {},
    #  u'project': u'yuankun/kf-gvcf-benchmarking',
    #  u'size': 53238342,
    #  u'storage': {u'location': u'1000G_omni2.5.hg38.vcf.gz',
    #               u'type': u'VOLUME',
    #               u'volume': u'yuankun/kf_references'},
    #  u'tags': [u'references']}
    f = file_
    return DataObject(
        checksums=[],
        created=f.created_on,
        updated=f.modified_on,
        file_name=f.name,
        file_size=str(f.size),
        urls=[
            URL(
                url=f.href,
                system_metadata=f._data.data)])


def cavataca_to_CreateDataObjectRequest(file_):
    """
    Takes a cavataca hit and creates a ga4gh CreateDataObjectRequest
    :param file_tuple:
    :return:
    """
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    create_request = CreateDataObjectRequest(
        data_object=cavataca_to_ga4gh(file_))
    return create_request


def post_cavataca(file_):
    """
    Takes a cavataca hit and indexes it into GA4GH.
    :param file_tuple:
    :return:
    """
    # try:
    create_request = cavataca_to_CreateDataObjectRequest(file_)
    if not args.dry_run:
        create_response = client.CreateDataObject(body=create_request).result()
        sys.stderr.write('.')
        sys.stderr.flush()
        return create_response
    else:
        print create_request


def load_cavataca(project_id, token, url):
    ''' get all files for all tasks, write to dos'''
    generator = CavatacaGenerator(project_id=project_id, token=token, url=url)
    for file_ in generator.files():
        post_cavataca(file_)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        description='Scrape Cavataca, populate webserver')
    common_args(argparser)
    custom_args(argparser)
    args = argparser.parse_args()
    local_client = client_factory(args)
    client = local_client.client
    models = local_client.models
    load_cavataca(
        project_id="yuankun/kf-gvcf-benchmarking",
        token=os.environ['SB_AUTH_TOKEN'],
        url='https://cavatica-api.sbgenomics.com/v2'
    )
