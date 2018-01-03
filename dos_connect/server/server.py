# Simple server implementation
import os

import connexion
from flask_cors import CORS

import argparse

import ga4gh.dos
# These are imported by name by connexion so we assert it here.
from ga4gh.dos.controllers import *  # noqa


def configure_app():
    app = connexion.App(
        __name__,
        swagger_ui=True,
        swagger_json=True)
    app.add_api(ga4gh.dos.server.SWAGGER_PATH)

    CORS(app.app)
    return app


def main(args):
    app = configure_app()
    app.run(port=args.port, debug=True)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='GA4GH dos_connect webserver')
    argparser.add_argument('-P', '--port', default=8080, type=int)
    main(argparser.parse_args())
