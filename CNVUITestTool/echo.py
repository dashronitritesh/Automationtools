"""Mock Echo Server to send responses to during development.

This script will start a mock flask server on localhost:8888 and
used by application to send continuous responses. This is used in absence of
a real response endpoint, like during development.

"""
import pprint
import logging
import random

from flask import Flask, request
from flask_restful import Api, Resource

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask("echo")
_api = Api(app)

pp = pprint.PrettyPrinter(indent=2)

class Echo(Resource):
    """Echo Endpoint resource"""

    def post(self):
        """Implementation of post method"""
        # Random blank lines to ensure stream of output is visible. Otherwise
        # it becomes fixed and seems logs aren't flowing.
        for i in range(1, random.randint(1, 3)):
            print()
        pp.pprint(request.json)
        # Same as above but after response output
        for i in range(1, random.randint(1, 3)):
            print()
        return "Success"


_api.add_resource(Echo, '/echo', endpoint='echo')

if __name__ == "__main__":
    app.run(port=8888)