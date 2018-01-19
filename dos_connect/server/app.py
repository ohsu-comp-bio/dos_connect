#!/usr/bin/python
# -*- encoding: utf-8 -*-

# Simple server implementation
import connexion
from flask_cors import CORS

import argparse
import sys
from OpenSSL import SSL

import ga4gh.dos
# These are imported by name by connexion so we assert it here.
from controllers import *  # noqa
# the swagger doc points to 'ga4gh.dos.server' module
# so, override it here.
sys.modules['ga4gh.dos.server'] = sys.modules[__name__]


def configure_app():
    """ associate swagger with app, setup CORS"""
    app = connexion.App(
        __name__,
        swagger_ui=True,
        swagger_json=True)
    app.add_api('data_objects_service.swagger.json')
    CORS(app.app)
    return app


def main(args):
    """ configure """
    app = configure_app()
    if args.key_file:
        context = (args.certificate_file, args.key_file)
        app.run(port=args.port, ssl_context=context)
    else:
        app.run(port=args.port)

if __name__ == '__main__':
    description = 'GA4GH dos_connect webserver'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('-P', '--port', default=8080, type=int)
    argparser.add_argument('-K', '--key_file', default=None)
    argparser.add_argument('-C', '--certificate_file', default=None)
    # argparser.add_argument('-A', '--authorizer',
    #                        default='dos_connect.server.basic_authorizer')
    # argparser.add_argument('-B', '--backend',
    #                        default='dos_connect.server.elasticsearch_backend')
    main(argparser.parse_args())
