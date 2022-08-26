# EA Testing

Mainly consist of four package `API`, `common`, `browser` & `response`.

## Code Overview

#### API
- Flask Rest API which exposes endpoints to `init`, `stop` or `action` work.
- All logic related to API is in `api` package
- `api` package structure
    - app.py            : Contains application & routes details.
    - listener.py       : Lister for API server. This how controller will start
                          API server
    - resource.py       : Flask restful resource for each type of Endpoint
    - service.py        : Service wrapper which has a task and response against
                          a request


#### Browser
- Contains browser details. Mainly scarapping details
- worker.py             : A worker against any Browser task which will scrape
                          UI and return response

#### Common
- Contains commong logic
- controller.py         : Controller which sets logger and starts all the listeners
- listener.py           : Base and ResponseListener.

#### Response
- Response engine runs and waits for any response task. Browser while scrapping
  creates a response task and put in queue.
- ResponseListener picks this task and does the job of sending response.
- worker.py             : Response worker level details

## Workflow

This is a sample workflow to run this application

1. Start the application engine
```
make run
```

2. Once application is running, initialize a connection
```
make init
```
This should start a new browser and return back when init step is complete.

3. Continue with different actions
```
make <action>
```

4. Close connection
```
make stop
```

## Internal Details


## Running on Windows
python3 -m venv /path/to/new/virtual/environment

"# Automationtools" 
