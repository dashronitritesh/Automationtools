import logging

from .app import app as apiApp
from common.listener import Listener

class APIListener(Listener):
    """
    Implementation of Listener class to start API server
    """

    _start_message = "Starting API Server at localhost:5443 ....."

    @staticmethod
    def run():
        """This method, runs flask api server"""
        apiApp.run(host='0.0.0.0', port=5443)
