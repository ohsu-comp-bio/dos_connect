# Simple server implementation
import os

import connexion
from flask_cors import CORS

import argparse
import sys

import ga4gh.dos
# These are imported by name by connexion so we assert it here.
from controllers import *  # noqa
# the swagger doc points to 'ga4gh.dos.server' module
# so, override it here.
sys.modules['ga4gh.dos.server'] = sys.modules[__name__]


def configure_app():
    app = connexion.App(
        __name__,
        swagger_ui=True,
        swagger_json=True)
    # ga4gh.dos.server.SWAGGER_PATH)
    app.add_api('data_objects_service.swagger.json')

    CORS(app.app)
    return app


def main(args):
    app = configure_app()
    app.run(port=args.port, debug=True)


if __name__ == '__main__':
    description = 'GA4GH dos_connect webserver'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('-P', '--port', default=8080, type=int)
    main(argparser.parse_args())
