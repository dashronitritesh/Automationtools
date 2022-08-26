run:
	python cli.py

echo:
	python echo.py

init:
	curl -i -X GET 'localhost:5443/test/init?callerNumber=15302149968'

takeover:
	curl -q \
		-d '{"type":"takeover", "data":"value2", "sessionId": "b1ba31e0-a70c"}' \
		-H "Content-Type: application/json" \
		-X POST \
		'localhost:5443/test/action'

menu:
	curl -q \
		-d '{"type":"menu", "data":{"name":"pasta"}}' \
		-H "Content-Type: application/json" \
		-X POST \
		'localhost:5443/test/action'
	# curl -q \
	# 	-d '{"type":"menu", "data":{"name":"bread"}}' \
	# 	-H "Content-Type: application/json" \
	# 	-X POST \
	# 	'localhost:5443/test/action'

submenu:
	curl -q \
		-d '{"type":"submenu", "data":{"name":"Chicken Alfredo Pasta"}}' \
		-H "Content-Type: application/json" \
		-X POST \
		'localhost:5443/test/action'
	# curl -q \
	# 	-d '{"type":"submenu", "data":{"name":"Stuffed Cheesy Bread"}}' \
	# 	-H "Content-Type: application/json" \
	# 	-X POST \
	# 	'localhost:5443/test/action'

add_to_summary:
	curl -q \
		-d '{"type":"add_to_summary", "data":{"id":"B8PCSCB"}}' \
		-H "Content-Type: application/json" \
		-X POST \
		'localhost:5443/test/action'
stop:
	curl -i -X GET 'localhost:5443/test/stop?sessionId=b1ba31e0-a70c-11ea-a8ed-b0359ff9a2f4'

demo:
	curl -i -X GET 'localhost:5000/test/init?callerNumber=1234567'
	sleep 10
	sleep 10

echo_test:

	curl -i \
		--header "Content-Type: application/json" \
		--request POST \
		--data '{"name": "okan"}' \
		http://localhost:8888/echo
