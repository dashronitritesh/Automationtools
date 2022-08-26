"""Handles control logic of the application

Mainly does two tihngs.
- Sets logger
- Start appropriate listeners. Currently it starts APIListener & ResponseListener
"""
import logging
import logging.handlers

from api.listener import APIListener
from response.listener import ResponseListener

class Controller:
    """
    Controller class contains control logic of application.

    Methods
    -------
    run()
        This classmethod, starts the controller. As part of starting it sets
        logger and start all the relevant listeners (API & Response)
    """

    _listeners = [APIListener, ResponseListener]
    _threads = []

    @staticmethod
    def _set_logger():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] p%(process)s %(levelname)s  %(module)s:%(lineno)d - %(message)s','%H:%M:%S')
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)


    @classmethod
    def run(cls):
        """Classmethod to run controller. This is the entrypoint of controller."""
        cls._set_logger()
        for listener in cls._listeners:
            listener.start(cls._threads)

        # Join to the threads to ensure applications doesn't terminate.
        for t in cls._threads:
            t.join()
