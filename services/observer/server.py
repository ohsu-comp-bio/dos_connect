#!/usr/bin/env python

"""
Observe object store updates from [swift,s3]
"""

import os

from flask import Flask, request, jsonify, Response, json
import requests

app = Flask(__name__)


# @app.errorhandler(ValidationError)
# def on_validation_error(e):
#     return "error"


@app.route('/swift', methods=['GET', 'POST'])
def swift():
    print request.json
    """Status Get the API status and version information"""
    return jsonify({
      "status": "OK"
    })


#  MAIN -----------------
if __name__ == '__main__':  # pragma: no cover
    app.run(debug=True)
