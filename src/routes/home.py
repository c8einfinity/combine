import os
from tina4_python.Router import get
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

@get("/")
async def index(request, response):
    request.session.set("logged_in", True)

    producer.produce({"event": "Hitting route"})
    return response("Ok")