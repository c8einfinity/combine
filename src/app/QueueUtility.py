import base64
import hashlib
import json
import os
import threading
from tina4_python import Debug
from tina4_python.Queue import Queue, Config, Consumer, Producer

config = Config()
config.queue_type = 'rabbitmq'
config.prefix = ""
config.rabbitmq_config = {
    'host': os.getenv('RABBITMQ_SERVER'),
    'port': 5672,
    'username': os.getenv('RABBITMQ_USERNAME'),
    'password': os.getenv('RABBITMQ_PASSWORD'),
}

def process_item(queue, err, msg):
    """
    Process the item from the queue
    :param queue:
    :param err:
    :param msg:
    :return:
    """
    from tina4_python.Database import Database
    if err is not None:
        Debug.error(f"Error processing message: {err}")
        return False

    try:
        message = json.loads(msg.data)
    except json.JSONDecodeError as e:
        Debug.error(f"Failed to decode message: {e}")
        return False

    if message is None:
        Debug.error("Message is None")
        return False

    action = message["action"]
    payload = message["payload"]
    dba = None

    if "action" in message:
        database_path = os.getenv("DATABASE_PATH", "db-mysql-nyc3-mentalmetrix-do-user-4490318-0.c.db.ondigitalocean.com/25060:qfinder")

        dba = Database(f"mysql.connector:{database_path}",
                       os.getenv("DATABASE_USERNAME", "doadmin"),
                       os.getenv("DATABASE_PASSWORD", "doadmin"))


    from src.app.Scraper import get_player_bio_urls, get_youtube_videos
    from src.orm.PlayerMedia import PlayerMedia
    from src.app.Player import get_player_transcript, split_trim_minify, submit_player_results
    from src.orm.Player import Player
    from src.orm.PlayerResult import PlayerResult
    from src.orm.Sport import Sport
    from src.orm.AdminSetting import AdminSetting


    if action == "process_player":
        player_id = payload["player_id"]
        Debug.info(f"Processing player from queue with ID: {player_id}")

        player = Player().select("*", filter="id = ?", params=[player_id], limit=1)
        if player.count == 0:
            Debug.error(f"Player {player_id} not found")
            return False

        player = player[0]

        bio_urls = get_player_bio_urls(str(player["first_name"]) + " " + str(player["last_name"]), player["sport"])

        for url in bio_urls:
            player_media = PlayerMedia({"url": url, "media_type": "link-bio", "player_id": player["id"]})

            if player_media.load("url = ? and player_id = ? and media_type = 'link-bio'", [url, player["id"]]):
                # exists
                pass
            else:
                player_media.is_valid = 1

            player_media.save()
            dba.commit()

        setting_query = "setting_key = 'video_sport_search_parameters'"
        if player["sport"]:
            sport = Sport().select("*", "name = ?", params=[str(player["sport"])], limit=1)
            if sport.count > 0:
                setting_query = f"setting_key = 'video_sport_{sport[0]["id"]}_search_parameters'"

        search_query_setting = AdminSetting().select("*", setting_query, limit=1)
        video_sport_search_criteria = str(player["sport"])
        if search_query_setting.count > 0:
            video_sport_search_criteria = search_query_setting[0]["setting_value"]

        you_tube_links = get_youtube_videos(str(player["first_name"]) + " " + str(player["last_name"]), video_sport_search_criteria)
        for you_tube_link in you_tube_links:
            player_media = PlayerMedia()
            player_media.url = you_tube_link["url"]
            player_media.player_id = player["id"]
            player_media.media_type = 'video-youtube'
            player_media.is_valid = 1
            player_media.metadata = you_tube_link["metadata"]
            player_media.save()
            dba.commit()

        player["is_video_links_created"] = 1
        player["is_bio_links_created"] = 1
        player = Player(player)
        player.image = None
        player.save()

    if action == "request_player_results":
        player_id = payload["player_id"]
        Debug.info(f"request_player_results {player_id}: Requesting player results start")
        player = None
        try:
            player = Player().select("*", filter="id = ?", params=[player_id], limit=1)
            if player.count == 0:
                Debug.error(f"request_player_results {player_id}: Player not found")
                queue_result = Queue(config, topic="result")
                Producer(queue_result).produce({"processed": True, "message_id": msg.message_id, "message": "OK"})
                raise Exception("Player not found")
            Debug.info(f"request_player_results {player_id}: Player loaded")
            player = player[0]
        except Exception as e:
            Debug.error(f"request_player_results {player_id}: Error loading player, {e}")

        if player is None:
            Debug.error(f"request_player_results {player_id}: Player not found")
            raise Exception("Player not found")

        Debug.info(f"request_player_results {player_id}: Player found")
        if player["image"]:
            player["image"] = player["image"]
        else:
            player.image = ""

        Debug.info(f"request_player_results {player_id}: Getting player transcript")

        transcript = get_player_transcript(player["id"])

        if transcript == "":
            Debug.error(f"request_player_results {player_id}: Transcript empty for player")

        try:
            Debug.info(f"request_player_results {player_id}: Transcript: {transcript}")
            transcription_hash = hashlib.md5(transcript.encode("utf-8")).hexdigest()
        except Exception as e:
            Debug.error(f"request_player_results {player_id}: Error hashing transcript, {e}")
            transcription_hash = ""

        Debug.info(f"request_player_results {player_id}: Transcript hash: {transcription_hash}")

        Debug.info(f"request_player_results {player_id}: Submitting player results to API")

        results = submit_player_results(
            str(player["first_name"]),
            str(player["last_name"]),
            str(player["image"]),
            str(transcript),
            str(player["candidate_id"]),
            str(player["sport"]),
            str(player["position"]),
            str(player["date_of_birth"]),
            str(player["home_town"]),
            str(player["team"])
        )

        Debug.info(f"request_player_results {player_id}: Player results received")

        if "candidate_id" in results:
            Debug.info(f"request_player_results {player_id}: Candidate ID: {results['candidate_id']}")
            player["image"] = player["image"].decode("utf-8")
            player = Player(player)
            player.candidate_id = results["candidate_id"]
            try:
                player.save()
            except Exception as e:
                Debug.error(f"request_player_results {player_id}: Error saving player, {e}")

        if "player" in results:
            results["player"]["html"] = split_trim_minify(results["player"]["html"])
            if "pdf" in results["player"]:
                del results["player"]["pdf"]
        if "coach" in results:
            results["coach"]["html"] = split_trim_minify(results["coach"]["html"])
            if "pdf" in results["coach"]:
                del results["coach"]["pdf"]
        if "scout" in results:
            results["scout"]["html"] = split_trim_minify(results["scout"]["html"])
            if "pdf" in results["scout"]:
                del results["scout"]["pdf"]

        Debug.info(f"request_player_results {player_id}: Saving player results to database")
        player_result = PlayerResult({
            "player_id": player_id,
            "transcript_hash": transcription_hash,
            "transcription": transcript,
            "data": json.dumps({"player": results["player"], "coach": results["coach"], "scout": results["scout"]})
        })
        player_result.save()
    if dba is not None:
        dba.commit()
        dba.close()

    queue_result = Queue(config, topic="result")
    Producer(queue_result).produce({"processed": True, "message_id": msg.message_id, "message": "OK"})
    queue.basic_ack(msg.delivery_tag)
    return None


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
        self.set_queue(os.getenv("RABBITMQ_QUEUE_NAME", "qfinder"))

    def connect(self):
        """
        Connect to RabbitMQ server and create a channel.
        """
        if config:
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
        print("Starting consumer")
        if self.queue is None:
            raise Exception("Queue is not connected")

        consumer = Consumer(self.get_queue(), process_item, acknowledge=False)
        consumer.run(sleep=int(os.getenv("RABBITMQ_CONSUMER_INTERVAL", 1)))

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

    try:
        consumer_thread = threading.Thread(target=consumer_thread)
        consumer_thread.start()
        Debug.info("Queue consumer started")
    except Exception as e:
        Debug.error(f"Error starting consumer thread: {e}")