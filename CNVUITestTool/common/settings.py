import queue

global task_queue
global worker_pool

task_queue = queue.Queue()
response_queue = queue.Queue()

worker_pool = {}

email = "rajalokan@gmail.com"
password = "Conversenow@123"
cnvtest_url = "http://localhost:6062/api/ea/ui/update"
eapos_url = "https://dt.staging.v2.conversenow.ai/operator"
blakes_url ="https://dt.staging.v2.conversenow.ai/"
drivethru_url = "https://drivethru.staging.conversenow.ai/employee"
drivethru_operator_url = "https://drivethru.staging.v2.conversenow.ai/operator"