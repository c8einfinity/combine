# Start your project here
import os
import threading
from tina4_python.Database import Database
from tina4_python.Migration import migrate
from tina4_python.ORM import orm
from tina4_python.Queue import Producer, Consumer

from .app.QueueUtility import tell_me
from .app.Setup import check_setup, check_players

database_path = os.getenv("DATABASE_PATH", "db-mysql-nyc3-mentalmetrix-do-user-4490318-0.c.db.ondigitalocean.com/25060:qfinder")

dba = Database(f"mysql.connector:{database_path}",
               os.getenv("DATABASE_USERNAME", "doadmin"),
               os.getenv("DATABASE_PASSWORD", "doadmin"))
migrate(dba)
orm(dba)

check_setup(dba)

# import everything

from .app import Setup, Utility, Scraper, QueueUtility
from .routes import athletes, dashboard, home, users, user_groups, websocket, queue

queue_instance = QueueUtility.QueueUtility()
# Start the queue consumer in a separate thread
def start_consumer():
    try:
        Consumer(queue_instance.get_queue(), tell_me).run(os.getenv("RABBITMQ_CONSUMER_INTERVAL", 10))
    except Exception as e:
        print("Error connecting to RabbitMQ queue: ", e)


consumer_thread = threading.Thread(target=start_consumer)
consumer_thread.start()