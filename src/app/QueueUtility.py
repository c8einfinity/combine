import hashlib
import json
import os
import threading
from tina4_python import Debug
from tina4_python.Queue import Queue, Config, Consumer, Producer

queue_config = Config()
queue_config.queue_type = 'mongo-queue-service'
queue_config.prefix = ""
queue_config.mongo_queue_config = {"host": os.getenv("MONGODB_HOST", "localhost"),
                             "port": int(os.getenv("MONGODB_PORT", 27017)),
                             "username": os.getenv("MONGODB_USERNAME", "admin"),
                             "password": os.getenv("MONGODB_PASSWORD", "password"),
                             "timeout": 300,
                             "max_attempts": 5}

def process_item(queue, err, msg):
    """
    Process the item from the queue
    :param queue:
    :param err:
    :param msg:
    :return:
    """
    from tina4_python.Database import Database

    Debug.info(f"Received message: {msg}", file_name="queue.log")

    if msg is None:
        Debug.error("Received None message", file_name="queue.log")
        return


    if err is not None:
        Debug.error(f"Error processing message: {err}", file_name="queue.log")
        return None

    try:
        message = json.loads(msg.data)
    except json.JSONDecodeError as e:
        Debug.error(f"Failed to decode message: {e}", file_name="queue.log")
        return None

    if message is None:
        Debug.error("Message is None", file_name="queue.log")
        return None


    action = message["action"]
    payload = message["payload"]
    dba = None

    if "action" in message:
        Debug.info(f"Processing action: {action}", file_name="queue.log")
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

    try:
        if action == "process_player":
            player_id = payload["player_id"]
            Debug.info(f"Processing player from queue with ID: {player_id}", file_name="queue.log")

            player = Player().select("*", filter="id = ?", params=[player_id], limit=1)
            if player.count == 0:
                Debug.error(f"Player {player_id} not found", file_name="queue.log")
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
                player_media.__dba__.commit()

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
            Debug.info(f"request_player_results {player_id}: Requesting player results start", file_name="queue.log")
            player = None
            try:
                player = Player().select("*", filter="id = ?", params=[player_id], limit=1)
                if player.count == 0:
                    Debug.error(f"request_player_results {player_id}: Player not found", file_name="queue.log")
                    queue_result = Queue(queue_config, topic="result")
                    Producer(queue_result).produce({"processed": True, "message_id": msg.message_id, "message": "OK"})
                    raise Exception("Player not found")
                Debug.info(f"request_player_results {player_id}: Player loaded", file_name="queue.log")
                player = player[0]
            except Exception as e:
                Debug.error(f"request_player_results {player_id}: Error loading player, {e}", file_name="queue.log")

            if player is None:
                Debug.error(f"request_player_results {player_id}: Player not found", file_name="queue.log")
                raise Exception("Player not found")

            Debug.info(f"request_player_results {player_id}: Player found", file_name="queue.log")
            if player["image"]:
                player["image"] = player["image"]
            else:
                player.image = ""

            Debug.info(f"request_player_results {player_id}: Getting player transcript", file_name="queue.log")

            transcript = get_player_transcript(player["id"])

            if transcript == "":
                Debug.error(f"request_player_results {player_id}: Transcript empty for player", file_name="queue.log")

            try:
                Debug.info(f"request_player_results {player_id}: Transcript characters: {len(transcript)}", file_name="queue.log")
                transcription_hash = hashlib.md5(transcript.encode("utf-8")).hexdigest()
            except Exception as e:
                Debug.error(f"request_player_results {player_id}: Error hashing transcript, {e}", file_name="queue.log")
                transcription_hash = ""

            Debug.info(f"request_player_results {player_id}: Transcript hash: {transcription_hash}", file_name="queue.log")

            Debug.info(f"request_player_results {player_id}: Submitting player results to API", file_name="queue.log")

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

            Debug.info(f"request_player_results {player_id}: Player results received", file_name="queue.log")

            if "error" in results:
                Debug.error(f"request_player_results {player_id}: Error in results: {results['error']}", file_name="queue.log")
                if results["error"] == "Position not found":
                    Debug.error(f"request_player_results {player_id}: Position not found, setting to 'None'", file_name="queue.log")
                    player["position"] = None
                    player = Player(player)
                    player.save()

            if "candidate_id" in results:
                Debug.info(f"request_player_results {player_id}: Candidate ID: {results['candidate_id']}", file_name="queue.log")
                player["image"] = player["image"].decode("utf-8")
                player = Player(player)
                player.candidate_id = results["candidate_id"]
                try:
                    player.save()
                except Exception as e:
                    Debug.error(f"request_player_results {player_id}: Error saving player, {e}", file_name="queue.log")

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

            Debug.info(f"request_player_results {player_id}: Saving player results to database", file_name="queue.log")
            player_result = PlayerResult({
                "player_id": player_id,
                "transcript_hash": transcription_hash,
                "transcription": transcript,
                "data": json.dumps({"player": results["player"], "coach": results["coach"], "scout": results["scout"]})
            })
            player_result.save()
    finally:
        queue_result = Queue(queue_config, topic="result")
        Producer(queue_result).produce({"processed": True, "message_id": msg.message_id, "message": "OK"})
        Debug.info(f"Acknowledging message: {msg.delivery_tag}", file_name="queue.log")
        queue.complete()
        Debug.info("Processing complete, committing changes to database", file_name="queue.log")
        if dba is not None:
            dba.close()
            return None


def message_delivered(queue, err, msg):
    """
    Callback for when a message is delivered
    :param queue: The queue instance
    :param err: Error if any occurred during delivery
    :param msg: The message that was delivered
    :return: True if message was delivered successfully, False otherwise
    """
    if err is not None:
        Debug.error(f"Error delivering message: {err}")
        return False

    Debug.info("Message delivered", file_name="queue.log")
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
        if queue_config:
            self.config = queue_config
        self.channel = None
        self.set_queue(os.getenv("MONGODB_QUEUE_DATABASE", "qfinder"))

    def set_queue(self, queue_name):
        """
        Set the queue name and create a queue instance.
        :param queue_name:
        :return:
        """
        if not self.config:
            raise Exception("Queue configuration is not set")

        if not queue_name:
            raise Exception("Queue name is not set")

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
        Debug.info(f"Adding item to queue: {message}", file_name="queue.log")
        Producer(self.queue, message_delivered).produce(message)


    def start_consumer(self, callback=None):
        """
        Start the consumer
        :param callback:
        :return:
        """
        Debug.info("Starting queue consumer", file_name="queue.log")
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
            Debug.info("Starting queue consumer thread", file_name="queue.log")
            queue_utility = QueueUtility()
            queue_utility.start_consumer()
        except Exception as e:
            Debug.error(f"Error in consumer thread: {e}", file_name="queue.log")

    try:
        # No need for a separate thread while testing
        # consumer_thread = threading.Thread(target=consumer_thread)
        # consumer_thread.start()
        consumer_thread()

        Debug.info("Queue consumer started", file_name="queue.log")
    except Exception as e:
        Debug.error(f"Error starting consumer thread: {e}", file_name="queue.log")