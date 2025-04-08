import json
import os
import threading
from tina4_python import Debug
from tina4_python.Queue import Queue, Config, Consumer, Producer

from src.app.Scraper import get_player_bio_urls, get_youtube_videos


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
    if err is not None:
        Debug.error(f"Error processing message: {err}")
        return False

    try:
        message = json.loads(msg.data)
    except json.JSONDecodeError as e:
        Debug.error(f"Failed to decode message: {e}")
        return False

    action = message["action"]
    payload = message["payload"]
    if action == "process_player":
        player_id = payload["player_id"]
        Debug.info(f"Processing player from queue with ID: {player_id}")
        from ..orm.Player import Player
        from ..orm.PlayerMedia import PlayerMedia

        player = Player().select("*", filter="id = ?", params=[player_id], limit=1)
        if player.count == 0:
            Debug.error(f"Player {player_id} not found")
            return False

        player = player[0]

        bio_urls = get_player_bio_urls(str(player.first_name) + " " + str(player.last_name))

        for url in bio_urls:
            player_media = PlayerMedia({"url": url, "media_type": "link-bio", "player_id": player.id})

            if player_media.load("url = ? and player_id = ? and media_type = 'link-bio'", [url, player.id]):
                # exists
                pass
            else:
                player_media.is_valid = 1

            player_media.save()

        you_tube_links = get_youtube_videos(str(player.first_name) + " " + str(player.last_name))
        for you_tube_link in you_tube_links:
            player_media = PlayerMedia()
            player_media.url = you_tube_link["url"]
            player_media.player_id = player.id
            player_media.media_type = 'video-youtube'
            player_media.is_valid = 1
            player_media.metadata = you_tube_link["metadata"]
            player_media.save()

        player.is_video_links_created = 1
        player.is_bio_links_created = 1
        player.save()
    return True


def message_delivered(queue, err, msg):
    """
    Callback for when a message is delivered
    :return:
    """
    if err is not None:
        Debug.error(f"Error delivering message: {err}")
        return False
    Debug.info("Message delivered")


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
        Debug.info(f"Adding item to queue: {message}")
        Producer(self.queue, message_delivered).produce(message)

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

