import json
import os
import tina4_python
from .. import dba
from ..app.Roles import Roles
from ..app.UserGroup import UserGroup
from tina4_python import Debug, tina4_auth
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

    html = Template.render("index.twig")
    return response(html)

@post("/login")
async def login(request, response):
    from src.orm.User import User
    user = User()

    if "email" in request.body and user.load("email = ?", [request.body["email"]]):
        # validating
        if  tina4_auth.check_password( str(user.password), request.body["password"]):
            user_group = UserGroup.get_user_group_data_by_id(user.user_group_id)

            if "permissions" in user_group and user_group["permissions"] and user_group["permissions"] != "None":
                permissions = json.loads(user_group["permissions"])
            else:
                permissions = Roles.get_initial_roles_permission_list()["access_list"]

            request.session.set("permissions", permissions)
            request.session.set("user", user.to_dict())

            return response("<script>window.location.href='/dashboard'</script>")
        else:
            return response('<div class="alert alert-danger">Error - not a user or not a password</div><script>$(".progress-spinner").hide();</script>')

    else:
        return response('<div class="alert alert-warning ">Error - not a user or not a password</div><script>$(".progress-spinner").hide();</script>')

@get("/logout")
async def get_logout(request, response):
    request.session.set("logged_in", False)
    request.session.set("user", None)

    return response.redirect("/")

@get("/session")
async def session(request, response):
    print("OK")
    print(request.session.get("logged_in"))


@get("/test/results")
async def index(request, response):
    from ..orm.PlayerMedia import PlayerMedia
    from ..app.Scraper import get_player_profile

    media = PlayerMedia().select(filter="player_id = ? and media_type = 'link-bio'", params=[1])
    collected_data = {"sport": "Football"}
    for player_media in media.to_list():
        collected_data = get_player_profile(player_media["url"], collected_data)
        dba.execute("update player_media set is_processed = 1, metadata = ? where id = ?", [collected_data, player_media["id"]])

    dba.commit()

    return response(collected_data)


@get("/test/pdf")
async def index(request, response):
    # import os
    # os.environ['PATH']='C:/Program Files/GTK3-Runtime Win64/bin/'+ os.pathsep + os.environ['PATH']
    # from weasyprint import HTML
    # HTML('https://qfinder.io/').write_pdf(tina4_python.root_path+'/output/login.pdf')
    #
    import pdfkit
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    pdfkit.from_url('https://qfinder.io/', tina4_python.root_path+'/output/login-pdfkit.pdf', configuration=config)

    return response("OK")

