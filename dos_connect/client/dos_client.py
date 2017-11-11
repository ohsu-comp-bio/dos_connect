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


def initialize(args):
    this_dir, this_filename = os.path.split(__file__)
    spec_dict = load_file(os.path.join(
                          this_dir, 'data_objects_service.swagger.json'))
    spec_dict['host'] = args.webserver_url

    models = SwaggerClient.from_spec(spec_dict,
                                     config=config)
    return models
