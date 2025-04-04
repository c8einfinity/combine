import os
from tina4_python import Debug
from tina4_python.Queue import Queue, Config

class QueueUtility(object):
    """
    This class is used to manage a queue for the application.
    It connects to RabbitMQ.
    """

    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.queue = None
        self.channel = None

    def connect(self):
        """
        Connect to RabbitMQ server and create a channel.
        """
        config = Config()
        config.queue_type = 'rabbitmq'
        config.prefix = ""
        config.rabbitmq_config = {
            'host': os.getenv('RABBITMQ_SERVER'),
            'port': 5672,
            'username': os.getenv('RABBITMQ_USERNAME'),
            'password': os.getenv('RABBITMQ_PASSWORD'),
        }

        self.queue = Queue(config, topic=self.queue_name)


    def tell_me(self, err, msg):
        Debug.info(err, msg)
