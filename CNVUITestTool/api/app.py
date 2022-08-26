"""Flask Application with routes for test actions"""
import logging

from flask import Flask
from flask_restful import Api

from api.resource import Init, Action, Stop

app = Flask(__name__)
_api = Api(app)

# Remove unnecessary flask debug logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

_api.add_resource(Init, '/test/init', endpoint='test-init')
_api.add_resource(Action, '/test/action', endpoint='test-action')
_api.add_resource(Stop, '/test/stop', endpoint='test-stop')

if __name__ == '__main__':
    app.run(host='0.0.0.0')

