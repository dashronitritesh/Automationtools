import logging
import time

from common.listener import Listener
from common import settings

class ResponseListener(Listener):
    """
    Implementation of Listener, which watches for a response task.
    ...
    Attributes
    ----------

    Methods
    -------
    run()
        Run a response task.
    """

    _start_message = "Starting Response Listener ....."

    @staticmethod
    def run():
        """Continous loop to look for a response task and serve it when available"""
        while True:
            # get global response queue
            response_queue = settings.response_queue
            # logging.info("Response queue size : %s" % response_queue.qsize())

            if not response_queue.empty():
                # If queue is not empty, get new task, serve it and mark it done
                next_task = response_queue.get()
                if next_task._worker.is_locked():
                    logging.info("Worker busy. Skipping it.")
                    response_queue.put(next_task)
                next_task.serve()
                response_queue.task_done()
            #time.sleep(2)



