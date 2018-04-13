#!/usr/bin/python
# -*- encoding: utf-8 -*-

# Simple server implementation
import connexion
from flask_cors import CORS

import argparse
import sys
from OpenSSL import SSL

from prometheus_client import generate_latest, Gauge

from flask import redirect

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
    # TODO get from schemas ga4gh.dos...? #24
    app.add_api('data_object_service.swagger.yaml')
    CORS(app.app)
    return app


def main(args):
    """ configure """
    app = configure_app()

    # create gauges for Prometheus
    # Responds with total counts
    gauges = {}
    for metric in metrics():
        g = Gauge('dos_connect_{}_count'.format(metric.name),
                  'Number of {}'.format(metric.name))
        g.set(metric.count)
        gauges[metric.name] = g

    # metrics
    # Prometheus server ping response
    @app.route('/metrics')
    def metrics_endpoint():
        for metric in metrics():
            g = gauges[metric.name]
            g.set(metric.count)
        return generate_latest()

    @app.route("/")
    def to_ui():
        return redirect("/ga4gh/dos/v1/ui", code=302)

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
    main(argparser.parse_args())
