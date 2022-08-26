import logging
import importlib
import time

from common import settings

TASK_TYPE_BROWSER = "BrowserTask"
TASK_TYPE_RESPONSE = "ResponseTask"


TASK_TO_WORKER_CLS_MAP = {
    TASK_TYPE_BROWSER: "browser.worker.BrowserWorker",
    TASK_TYPE_RESPONSE: "response.worker.ResponseWorker",
}

STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"

ERR_MSG_INTERNAL_SERVER_ERR = "Internal Server Error"

class Response:
    """
    A standard response class for all endpoints.

    This will be attached to each request and filled with relevant response
    details during the course of execution. Finally this wil be returned as a
    return of request.
    """
    def __init__(self, status=None, session_id=None, data={}, message=""):
        self.status = status
        self.session_id = session_id
        self.message = message
        self.data = data

class Task:
    """
    Base Task class.

    Parameters
    ----------

    Methods
    -------
    New(dict)
        Service method to generate an instance of a particular task type.
    serve()
        Method to serve a task. As part of serving set response status and
        execute the worker for this class.
    execute_browser_task(args, kwargs)
        A staticmethod to execute a browser task. Here a BrowserTask instance
        will be created and served.

    """
    _type = None
    _worker = None
    _params = {}
    _response = Response()

    def __init__(self, session_id):
        if not self._worker:
            module_name, cls_name = TASK_TO_WORKER_CLS_MAP[self._type].rsplit(".", 1)
            cls = getattr(importlib.import_module(module_name), cls_name)
            self._worker = getattr(cls, 'get_instance')(session_id)
            self._worker._session_id = session_id
        self._response = Response(session_id=session_id)

    @staticmethod
    def New(task_type, **kwargs):
        if task_type == TASK_TYPE_BROWSER:
            return BrowserTask(**kwargs)
        elif task_type == TASK_TYPE_RESPONSE:
            return ResponseTask(**kwargs)

    def serve(self):
        try:
            self._response.status = STATUS_SUCCESS
            self._worker.execute(self._params, self._response)
        except Exception as err:
            logging.exception(err)
            self._response.status = STATUS_FAILED
            self._response.message = ERR_MSG_INTERNAL_SERVER_ERR

    @staticmethod
    def execute_browser_task(**kwargs):
        """
        A staticmethod to execute a browser task. Here a BrowserTask instance
        will be created and served.

        Parameters
        ----------
        args: args
            Nothing here
        kwargs: kwargs
            task_type: str
                Type of the task either `BrowserTask` or `ResponseTask`
            anything else as a dict which will be passed to worker instance
        """
        task_type = kwargs.pop('task_type')
        task = Task.New(task_type, **kwargs)
        task.serve()

        # Another way is to run this asynchrounus like below. Since we want a
        # synchronous flow now, we will serve this immediately.
        # # task_queue = settings.task_queue
        # # task_queue.put(task)
        # # while not task._is_initialized():
        # #     time.sleep(2)

        return task._response

    @staticmethod
    def add_response_task(*args, **kwargs):
        """
        A staticmethod to add a response task. Here a ResponseTask instance
        will be created and put to queue.

        Parameters
        ----------
        args: args
            Nothing here
        kwargs: kwargs
            task_type: str
                Type of the task either `BrowserTask` or `ResponseTask`
            session_id: str
                Session ID for this task
            anything else as a dict which will be passed to worker instance
        """
        task_type = kwargs.pop('task_type')
        task = Task.New(task_type, **kwargs)
        response_queue = settings.response_queue
        response_queue.put(task)

    def _is_initialized(self):
        return self._worker._is_initialized

class BrowserTask(Task):
    _type = TASK_TYPE_BROWSER

    def __init__(self, **kwargs):
        session_id = kwargs.pop('session_id')
        self._params = kwargs
        super().__init__(session_id)

class ResponseTask(Task):
    _type = TASK_TYPE_RESPONSE

    def __init__(self, session_id, *args, **kwargs):
        self._params = kwargs
        super().__init__(session_id)

