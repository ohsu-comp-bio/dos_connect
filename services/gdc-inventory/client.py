# Simple client usage via bravo

import os
from bravado.client import SwaggerClient
from bravado.swagger_model import load_file
config = {
    'validate_requests': False,
    'validate_responses': False,
    'use_models': False
}

# URL = 'http://localhost:8080'
# models = SwaggerClient.from_url('{}/swagger.json'.format(URL), config=config)

spec_dict = load_file('data_objects_service.swagger.json')
spec_dict['host'] = '{}:{}'.format('localhost', '8080')

models = SwaggerClient.from_spec(spec_dict,
                                 config=config)
client = models.DataObjectService

"""
import client
import requests
import json
models = client.models
client = client.client
ListDataObjectRequest = models.get_model('ga4ghListDataObjectsRequest')
listDataObjectRequest = ListDataObjectRequest(url='file://exahead1/home/exacloud/lustre1/SMMARTData/Patients/16113-101/fastq/LIB170201PS_TB78_Buffy_S1_R2_001.fastq.gz')
client.ListDataObjects(body=listDataObjectRequest).result()
"""
