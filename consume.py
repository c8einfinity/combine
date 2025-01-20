import os
from tina4_python.Queue import Queue, Config, Consumer

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

def callback(_queue, err, body):
    print(body.data)

consumer = Consumer(queue, callback)
consumer.run()