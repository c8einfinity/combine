import os
from tina4_python import Debug
from tina4_python.Queue import Queue, Config


def tell_me(queue, err, msg):
    Debug.info(err, msg)


class QueueUtility(object):
    """
    This class is used to manage a queue for the application.
    It connects to RabbitMQ.
    """
    queue = None

    def __init__(self):
        self.queue_name = ""
        self.config = None
        self.channel = None
        self.connect()
        self.set_queue("qfinder")

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

        self.config = config

    def set_queue(self, queue_name):
        """
        Set the queue name and create a queue instance.
        :param queue_name:
        :return:
        """
        self.queue = Queue(self.config, queue_name)

    def get_queue(self):
        """
        Get the queue, throw an exception if it is empty
        :return: Queue
        """
        if self.queue is None:
            raise Exception("Queue is not connected")
        return self.queue
