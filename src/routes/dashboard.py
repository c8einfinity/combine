from tina4_python.Constant import HTTP_OK, TEXT_HTML
from tina4_python.Queue import Producer
from tina4_python.Template import Template
from tina4_python.Router import get, post
import random
import json


@get("/dashboard")
async def get_dashboard(request, response):
    """
    Get the dashboard
    :param request:
    :param response:
    :return:
    """
    # Temp example to test the queue
    # from ..app.QueueUtility import QueueUtility
    # queue_instance = QueueUtility()
    # Producer(queue_instance.get_queue()).produce("A test message")
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    return response(Template.render_twig_template("dashboard.twig"))


@get("/dashboard/home")
async def get_dashboard_home(request, response):
    """
    Get the home grid for the dashboard
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    from ..app.Queue import get_total_transcribed_stats
    from ..app.Player import get_player_stats

    total_transcribed_stats = get_total_transcribed_stats()

    player_stats = get_player_stats()

    return response(Template.render_twig_template("dashboard/home.twig",
                                                  data={"total_transcribed_stats": total_transcribed_stats,
                                                        "player_stats": player_stats}))


@get("/dashboard/athletes/{status}")
async def get_dashboard_athletes(request, response):
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    html = Template.render_twig_template("dashboard/athletes.twig", data={"status": request.params["status"]})

    return response(html)


@get("/dashboard/queue")
async def get_dashboard_queue(request, response):
    """
    Get the queue grid for the dashboard
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    return response(Template.render_twig_template("dashboard/queue.twig"))


def decode_metadata(record):
    """
    Decodes the metadata from the video
    :param record:
    :return:
    """
    record["metadata"] = json.loads(record["metadata"])
    record["title"] = record["metadata"]["items"][0]["snippet"]["title"]
    record["description"] = record["metadata"]["items"][0]["snippet"]["description"]
    record["published_at"] = record["metadata"]["items"][0]["snippet"]["publishedAt"]
    return record


@get("/media/sorter")
async def get_media_sorter(request, response):
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Player import Player
    skip = random.randint(1, 5)

    counter = request.session.get("counter")

    if counter is None:
        counter = 1

    videos = PlayerMedia().select(limit=1, skip=skip,
                                  filter="media_type like 'video%' and is_deleted = 0 and is_sorted = 0")

    if videos.count > 0:
        video = videos.to_list(decode_metadata)[0]
        player = Player({"id": video["player_id"]})
        player.load()

    else:
        video = None

    html = Template.render_twig_template("media/sorter.twig",
                                         {"video": video, "player": player.to_dict(), "counter": counter})

    return response(html)


@post("/media/sorter")
async def post_media_sorter(request, response):
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Queue import Queue

    counter = request.session.get("counter")
    if counter is None:
        request.session.set("counter", 1)
    else:
        request.session.set("counter", counter + 1)

    player_media = PlayerMedia({"id": request.body["player_media_id"]})
    player_media.load()

    if request.body["is_valid"] == "1":
        player_media.is_valid = 1

        queue = Queue()
        if not queue.load("player_media_id = ?", [request.body["player_media_id"]]):
            queue.action = 'transcribe'
            queue.player_id = request.body["player_id"]
            queue.data = {"player_media_id": request.body["player_media_id"]}
            queue.save()

    else:
        player_media.is_valid = 0
        player_media.is_deleted = 1

    player_media.is_sorted = 1
    player_media.save()

    return response.redirect("/media/sorter")

