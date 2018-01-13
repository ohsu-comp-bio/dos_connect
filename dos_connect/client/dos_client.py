
from bravado.client import SwaggerClient


DEFAULT_CONFIG = {
    'validate_requests': False,
    'validate_responses': False
}


class Client:
    """
    simple wrapper around bravado swagger Client see
    https://github.com/Yelp/bravado/blob/master/docs/source/configuration.rst#client-configuration
    https://github.com/Yelp/bravado#example-with-basic-authentication
    """
    def __init__(self, url, config=DEFAULT_CONFIG, http_client=None):
        swagger_path = '{}/swagger.json'.format(url.rstrip("/"))
        self._config = config
        self.models = SwaggerClient.from_url(swagger_path,
                                             config=config,
                                             http_client=http_client)
        self.client = self.models.DataObjectService
