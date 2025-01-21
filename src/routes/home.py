import os
from tina4_python import Debug
from tina4_python.Router import get, post
from tina4_python.Queue import Queue, Config, Producer
from tina4_python.Template import Template

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

def tell_me(queue, err, msg):
    Debug.info(err, msg)

producer = Producer(queue, delivery_callback=tell_me)

@get("/")
async def index(request, response):
    request.session.set("logged_in", False)

    html = Template.render_twig_template("index.twig")
    return response(html)

@post("/login")
async def login(request, response):
    request.session.set("logged_in", True)
    return response("<script>window.location.href='/dashboard'</script>")




@get("/session")
async def session(request, response):
    print("OK")
    print(request.session.get("logged_in"))
