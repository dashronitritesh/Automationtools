#!/usr/bin/env python3

import requests

init_url = 'http://localhost:5443/test/init?callerNumber=15302149968'

# First session
first_response = requests.get(init_url)
first_session_id = first_response.json()['session_id']
# first_session_id = '50f3346c-a962-11ea-a8ed-b0359ff9a2f4'

# Second session
second_response = requests.get(init_url)
second_session_id = second_response.json()['session_id']

# Takeover First session
action_url = 'http://localhost:5443/test/action'
data = {
    "type": "takeover",
    "data": "value2",
    "sessionId": first_session_id
}
requests.post(action_url, data=data)

# Stop First Session
stop_url = "http://localhost:5443/test/stop"
params = {
    'sessionId': first_session_id
}
requests.get(stop_url, params=params)

