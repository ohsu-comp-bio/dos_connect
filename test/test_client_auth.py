
# With app.py running start this test
import logging
import sys
import os
import uuid

# setup connection, models and security
from bravado.requests_client import RequestsClient
from dos_connect.client.dos_client import Client

# setup logging
root = logging.getLogger()
root.setLevel(logging.ERROR)
logging.captureWarnings(True)

config = Client.config('https://localhost/')


print 'securityDefinitions:'
if 'securityDefinitions' not in config:
    print 'no authentication'
else:
    securityDefinitions = config.get('securityDefinitions', {}).keys()
    print securityDefinitions


def _finditem(obj, key):
    if key in obj:
        return obj[key]
    for k, v in obj.items():
        if isinstance(v, dict):
            return _finditem(v, key)

print 'security use:'
print [s.keys()[0] for s in _finditem(config, 'security')]

# http_client.set_api_key('localhost', 'XXX-YYY-ZZZ', param_in='header')
# local_client = Client('https://localhost/', http_client=http_client)
# client = local_client.client
# models = local_client.models
