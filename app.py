from tina4_python import *

from src.app.QueueUtility import start_queue_consumer

start_queue_consumer()

print("Running the service", sys.argv)
default_port = 8080
if len(sys.argv) > 2:
    default_port = int(sys.argv[2])
run_web_server("0.0.0.0", default_port)
