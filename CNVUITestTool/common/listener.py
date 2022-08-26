"""Contains common listeners of applications namely TaskListener & ResponseListener
"""
import threading
import logging


# TODO: Make run() method abstract of Listener

class Listener:
    """Base Listener class which has logic to start a listener."""

    @classmethod
    def start(cls, threads):
        """
        start() method, starts a daemon thread and add this thread to
        threads parameters provided.

        This is to maintain a separate list of
        active threads.

        Parameters
        ----------
        threads : list
            A list of active threads. Any new thread started will be added ot it.
        """
        logging.info(cls._start_message)
        t = threading.Thread(target=cls.run)
        t.setDaemon(True)
        t.start()

        threads.append(t)
