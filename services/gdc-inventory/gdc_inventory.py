# With app.py running start this demo
import client

import requests
import json

models = client.models
client = client.client

GDC_URL = 'https://api.gdc.cancer.gov'

# """
# {
#     "access": "open",
#     "acl": [
#       "open"
#     ],
#     "analysis": {
#       "input_files": [
#         {
#           "md5sum": "29d54c860372247a7fd15ce617defe2d"
#         }
#       ],
#       "workflow_link": "https://github.com/NCI-GDC/mirna-profiler",
#       "workflow_type": "BCGSC miRNA Profiling"
#     },
#     "cases": [
#       {
#         "diagnoses": [
#           {
#             "morphology": "8170/3",
#             "primary_diagnosis": "c22.0"
#           }
#         ],
#         "samples": [
#           {
#             "sample_id": "71bc4fd0-374f-423e-a8b4-ae1bceceda83"
#           }
#         ]
#       }
#     ],
#     "created_datetime": "2017-08-15T17:07:36.292672-05:00",
#     "data_category": "Transcriptome Profiling",
#     "data_format": "TSV",
#     "data_type": "Isoform Expression Quantification",
#     "error_type": null,
#     "experimental_strategy": "miRNA-Seq",
#     "file_id": "9c51ff3a-6c88-4f17-9c33-c630a6d10ea3",
#     "file_name": "95eaeaf5-ac6b-47bb-900a-a567e9a20b17.mirbase21.isoforms.quantification.txt",
#     "file_size": 217757,
#     "file_state": "submitted",
#     "id": "9c51ff3a-6c88-4f17-9c33-c630a6d10ea3",
#     "md5sum": "4abd5f25e53360867bd7a51e60c97219",
#     "state": "live",
#     "state_comment": null,
#     "submitter_id": "95eaeaf5-ac6b-47bb-900a-a567e9a20b17_isoform_profiling",
#     "type": "mirna_expression",
#     "updated_datetime": "2017-08-15T17:07:36.292672-05:00"
# }
# """


def gdc_to_data_object(gdc):
    """
    Accepts a gdc dictionary and returns a CreateDataObjectRequest
    :return:
    """
    DataObject = models.get_model('ga4ghDataObject')
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    URL = models.get_model('ga4ghURL')
    Checksum = models.get_model('ga4ghChecksum')
    url = URL(url="{}/data/{}".format(GDC_URL, gdc.get('file_id')),
              system_metadata=gdc)
    data_object = DataObject(
        id=url,
        checksums=[Checksum(checksum=gdc.get('md5sum'), type='md5')],
        file_name=gdc.get('file_name'),
        file_size=str(gdc.get('file_size')),
        aliases=[gdc['file_id']],
        urls=[url])
    return data_object


def gdc_to_ga4gh(gdc):
    """
    Accepts a gdc dictionary and returns a CreateDataObjectRequest
    :return:
    """
    DataObject = models.get_model('ga4ghDataObject')
    CreateDataObjectRequest = models.get_model('ga4ghCreateDataObjectRequest')
    URL = models.get_model('ga4ghURL')
    Checksum = models.get_model('ga4ghChecksum')
    print(str(gdc.get('file_size')))
    create_data_object = DataObject(
        checksums=[Checksum(checksum=gdc.get('md5sum'), type='md5')],
        file_name=gdc.get('file_name'),
        file_size=str(gdc.get('file_size')),
        aliases=[gdc['file_id']],
        urls=[
            URL(
                url="{}/data/{}".format(GDC_URL, gdc.get('file_id')),
                system_metadata=gdc)])
    create_request = CreateDataObjectRequest(data_object=create_data_object)
    return create_request


def post_gdc(gdc):
    """
    Takes a GDC hit and indexes it into GA4GH.
    :param gdc:
    :return:
    """
    create_request = gdc_to_ga4gh(gdc)
    create_response = client.CreateDataObject(body=create_request).result()
    return create_response


def post_kafka(gdc):
    """
    Takes a GDC hit and indexes it into GA4GH.
    :param gdc:
    :return:
    """
    data_object = gdc_to_data_object(gdc)
    print json.dumps(data_object.marshal(), indent=2, sort_keys=True)
    return data_object


def load_gdc():
    """
    Gets data from GDC and loads it to DOS.
    :return:
    """
    response = requests.post(
        '{}/files?related_files=true'.format(GDC_URL), json={}).json()
    hits = response['data']['hits']
    # Initialize to kick off paging
    pagination = {}
    pagination['pages'] = 1
    pagination['page'] = 0
    page_length = 10
    while int(pagination.get('page')) < int(pagination.get('pages')):
        map(post_gdc, hits)
        next_record = pagination.get('page') * page_length
        fields = 'access,acl,created_datetime,data_category,data_format,' \
            'data_type,error_type,experimental_strategy,file_id,' \
            'file_name,file_size,file_state,md5sum,origin,' \
            'platform,revision,state,state_comment,submitter_id,' \
            'tags,type,updated_datetime,' \
            'cases.samples.sample_id,' \
            'analysis.workflow_type,analysis.workflow_link,' \
            'analysis.input_files.md5sum,' \
            'cases.project_id,cases.diagnoses.morphology,' \
            'cases.diagnoses.primary_diagnosis'
        url = '{}/files?related_files=true&from={}&fields={}' \
            .format(GDC_URL, next_record, fields)
        print url
        response = requests.post(url, json={}).json()
        hits = response['data']['hits']
        pagination = response['data']['pagination']


if __name__ == '__main__':
    load_gdc()
