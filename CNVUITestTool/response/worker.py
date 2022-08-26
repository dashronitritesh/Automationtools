import logging
import time
import requests

from selenium import webdriver

from common.settings import cnvtest_url


class ResponseWorker:
    """
    Contains worker execution logic for a response task.

    This is a singlenton class. We don't necessarily need this to be singlenton
    but other worker in application (BrowserWorker) is singlenton so made this
    singlenton as well. This is way both will be same.
    ...
    Attributes
    ----------

    Methods
    -------
    get_instance()
        Return a new instance or existing singlenton instance of class
    execute(dict, obj<response>)
        Executes the response task by preparing post body and posting it to
        appropriate target url.
    is_locked()
        Method to check if there is another task running by this worker.
    """

    __instance = None

    _lock = False

    def __init__(self):
        if ResponseWorker.__instance is None:
            ResponseWorker.__instance = self

    @staticmethod
    def get_instance(session_id=None):
        """Creates a new instance or return singlenton instance of class"""
        if ResponseWorker.__instance == None:
            ResponseWorker()
        return ResponseWorker.__instance

    def execute(self, params, response):
        """
        Execution logic for a response task.

        Parameters
        ----------
        params : dict
            A key/value of parameters. These will be used to send post data.
        response : obj<response>
            A response object. Not needed for this worker.
        """
        self._available = False
        logging.debug("ResponseWorker - Sending response")
        data = {
            'status': "SUCCESS",
            'session_id': response.session_id,
            'data': params['data'],
            'updateTime': params['update_time'],
            'message': ""
        }
        try:
            requests.post(cnvtest_url, json=data)
            #requests.post(url2, json=data)
        except Exception as e:
            logging.error("Error while while posting to %s" % cnvtest_url)
        self._available = True

    def is_locked(self):
        """Check if worker is locked for execution"""
        return self._lock

