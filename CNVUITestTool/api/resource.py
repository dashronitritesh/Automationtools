import logging
import uuid

from flask import request
from flask_restful import Resource, reqparse, fields, marshal_with

from api.service import Task

resource_fields = {
    'status': fields.String(),
    'session_id': fields.String,
    'message': fields.String(default=""),
    # TODO: Convert this data from string to dict. fields.Nested...
    'data': fields.String,
}


class Init(Resource):
    """Flask Resource for Init endpoint"""

    def __init__(self):
        self._parser = reqparse.RequestParser()
        # self._parser.add_argument('callerNumber',
        #     type=str,
        #     required=True,
        #     help="callerNumber cannot be blank!!"
        # )
        self._parser.add_argument('data',
            type=str,
            required=True,
            help="data field cannot be blank!!"
        )

    @marshal_with(resource_fields)
    def post(self):
        """Standard GET method for flask Resource class"""
        args = self._parser.parse_args(strict=True)
        #caller_number = args['callerNumber']
        session_id = str(uuid.uuid1())
        logging.info("%s - Received request for %s action" %(session_id, 'init'))
        params = {
            'task_type':  'BrowserTask',
            'session_id': session_id,
            'action': 'init',
            #'caller_number': caller_number,
            'data': args['data'],
        }
        return Task.execute_browser_task(**params)

class Action(Resource):
    """Flask Resource for Action endpoint"""

    def __init__(self):
        self._parser = reqparse.RequestParser()
        self._parser.add_argument('type',
            type=str,
            required=True,
            help="type field cannot be blank!!"
        )
        self._parser.add_argument('data',
            type=str,
            required=True,
            help="data field cannot be blank!!"
        )
        self._parser.add_argument('sessionId',
            type=str,
            required=True,
            help="sessionId field cannot be blank!!"
        )

    @marshal_with(resource_fields)
    def post(self):
        """Standard POST method for flask Resource class"""
        logging.debug("Action Request")
        args = self._parser.parse_args()
        action = args['type']
        session_id = args['sessionId']
        logging.debug(session_id)
        params = {
            'task_type':  'BrowserTask',
            'session_id': session_id,
            'action': action,
            'data': args['data'],
        }
        return Task.execute_browser_task(**params)

class Stop(Resource):
    """Flask Resource for Stop endpoint"""

    def __init__(self):
        self._parser = reqparse.RequestParser()
        self._parser.add_argument('sessionId',
            type=str,
            required=True,
            help="type field cannot be blank!!"
        )

    @marshal_with(resource_fields)
    def get(self):
        """Standard GET method for flask Resource class"""
        args = self._parser.parse_args(strict=True)
        session_id = args['sessionId']
        logging.info("%s - Received request for %s action" %(session_id, 'stop'))
        params = {
            'task_type':  'BrowserTask',
            'session_id': session_id,
            'action': 'close',
        }
        return Task.execute_browser_task(**params)

