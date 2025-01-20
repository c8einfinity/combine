import sys
import os
from tina4_python import *
from tina4_python.Queue import Queue, Config, Producer

config = Config()
config.queue_type = 'rabbitmq'
config.prefix = ""
config.rabbitmq_config = {
    'host': os.getenv('RABBITMQ_SERVER'),
    'port': 5672,
    'username': os.getenv('RABBITMQ_USERNAME'),
    'password': os.getenv('RABBITMQ_PASSWORD'),
}

queue = Queue(config, topic="server-start")

producer = Producer(queue)
producer.produce({"event": "Sever started"})

print("Running the service", sys.argv)
default_port = 8118
if len(sys.argv) > 2:
    default_port = int(sys.argv[2])
run_web_server("0.0.0.0", default_port)