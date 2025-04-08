import json
import os
import threading
import asyncer
from tina4_python import Debug
from tina4_python.Queue import Queue, Config, Consumer, Producer


def start_queue_consumer():
    """
    Start the QueueUtility consumer in a separate thread.
    :return:
    """
    def consumer_thread():
        try:
            queue_utility = QueueUtility()
            queue_utility.start_consumer()
        except Exception as e:
            Debug.error(f"Error in consumer thread: {e}")

    consumer_thread = threading.Thread(target=consumer_thread, daemon=True)
    consumer_thread.start()


def process_item(queue, err, msg):
    """
    Process the item from the queue
    :param queue:
    :param err:
    :param msg:
    :return:
    """
    if err:
        Debug.error(f"Error processing message: {err}")
        return False

    try:
        message = json.loads(msg)
    except json.JSONDecodeError as e:
        Debug.error(f"Failed to decode message: {e}")
        return False

    action = message["action"]
    payload = message["payload"]
    if action == "process_player":
        player_id = payload["player_id"]
        Debug.info(f"Processing player from queue with ID: {player_id}")
        player = Player()
        player.select("*", filter="id = ?", params=[player_id], limit=1)
        if player.count == 0:
            Debug.error(f"Player with ID {player_id} not found")
            return False
        player = player.to_dict()


    return True


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

    def add_item(self, action, payload):
        """
        Add an item to the queue
        :param action:
        :param payload:
        :return:
        """
        if self.queue is None:
            raise Exception("Queue is not connected")
        message = json.dumps({"action": action, "payload": payload})

        Producer(self.queue).produce(message)

    def start_consumer(self, callback=None):
        """
        Start the consumer
        :param callback:
        :return:
        """
        if self.queue is None:
            raise Exception("Queue is not connected")
        consumer = Consumer(self.get_queue(), process_item)
        consumer.run(sleep=int(os.getenv("RABBITMQ_CONSUMER_INTERVAL", 10)))

