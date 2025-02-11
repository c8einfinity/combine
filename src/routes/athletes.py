import json
from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_HTML, TEXT_PLAIN, HTTP_OK
from tina4_python.Template import Template
from tina4_python.Router import get, post, delete
import base64
from ..app.Scraper import get_speaker_from_transcript, get_classification_text
from ..app.Utility import get_data_tables_filter
from .. import dba

@get("/api/athletes")
async def get_athletes(request, response):
    if "draw" not in request.params:
        return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

    from ..orm.Player import Player

    data_tables_filter = get_data_tables_filter(request)

    where = "id <> ?"
    if data_tables_filter["where"] != "":
        where += " and "+data_tables_filter["where"]

    players = Player().select(["id", "first_name", "last_name", "date_of_birth", "sport", "home_town", "major"],
                                where,
                              [0],
                              order_by=data_tables_filter["order_by"],
                              limit=data_tables_filter["length"],
                              skip=data_tables_filter["start"],)

    data = players.to_paginate()

    data["draw"] = request.params["draw"]

    return response (data)

def decode_metadata(record):
    record["metadata"] = json.loads(record["metadata"])
    record["title"] = record["metadata"]["items"][0]["snippet"]["title"]
    record["description"] = record["metadata"]["items"][0]["snippet"]["description"]
    record["published_at"] = record["metadata"]["items"][0]["snippet"]["publishedAt"]
    transcript = dba.fetch_one("select * from player_transcripts where player_media_id = ?", [record["id"]])
    if transcript:
        record["transcript"] = json.loads(base64.b64decode(transcript["data"]))
    else:
        record["transcript"] = None

    return record

def decode_transcript(record):
    record["data"] = json.loads(base64.b64decode(record["data"]))
    return record


@get("/api/athletes/{id}")
async def get_athlete(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia

    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video%' and is_deleted = 0 ", params=[request.params["id"]])
    player = Player({"id": request.params["id"]})


    # return response({"player": player.to_dict(), "videos": videos.to_list(decode_metadata)})
    if player.load():
        html = Template.render("player/profile.twig", {"player": player.to_dict(), "videos": videos.to_list(decode_metadata)})
        return response(html)
    else:
        return response("Player error, or player not found")

@get("/api/athletes/{id}/videos")
async def get_athlete_videos(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video%' and is_deleted = 0 ", params=[request.params["id"]])
    player = Player({"id": request.params["id"]})
    html = Template.render("player/videos.twig", {"player": player.to_dict(), "videos": videos.to_list(decode_metadata)})
    return response(html)


@get("/api/athletes/{id}/videos/{video_id}/transcript")
async def get_athlete_transcripts(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.PlayerTranscripts import PlayerTranscripts
    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and id = ? and is_deleted = 0 ", params=[request.params["id"], request.params["video_id"]])
    player = Player({"id": request.params["id"]})
    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and player_media_id = ?', params=[request.params["id"], request.params["video_id"]])

    if videos.count > 0:
        video = videos.to_list(decode_metadata)[0]
    else:
        video = None

    html = Template.render("player/video-transcript.twig", {"player": player.to_dict(), "video": video, "transcripts": player_transcripts.to_list(decode_transcript)})
    return response(html)

@post("/api/athletes/{id}/videos/{video_id}/transcript/queue")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.Queue import Queue

    queue = Queue()

    if not queue.load("player_media_id", [request.params["video_id"]]):
        queue.action = 'transcribe'
        queue.player_id = request.params["id"]
        queue.data = {"player_media_id": request.params["video_id"]}
        queue.save()
    return response("Queued!")

@post("/api/athletes/{id}/videos/{video_id}/remove")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["video_id"]})
    if player_media.load():
        player_media.is_deleted = 1
        player_media.save()

    return response("Removed!")

@post("/api/athletes/{id}/videos/{video_id}/include")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["video_id"]})
    if player_media.load():
        if player_media.is_valid:
            player_media.is_valid = 0
        else:
            player_media.is_valid = 1

        player_media.save()

    return response("Done!")


@get("/api/athletes/{id}/links")
async def get_athlete_links(request, response):
    if "draw" not in request.params:
        return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

    from ..orm.PlayerMedia import PlayerMedia

    data_tables_filter = get_data_tables_filter(request)

    where = "id <> ? and player_id = ?"
    if data_tables_filter["where"] != "":
        where += " and "+data_tables_filter["where"]

    player_media = PlayerMedia().select(["id", "url", "media_type", "player_id", "is_valid", "date_created"],
                                        where,
                                        [0, request.params["id"]],
                                        order_by=data_tables_filter["order_by"],
                                        limit=data_tables_filter["length"],
                                        skip=data_tables_filter["start"],)

    data = player_media.to_paginate()

    data["draw"] = request.params["draw"]

    return response (data)


@post("/api/athletes")
async def post_athletes(request, response):
    from ..orm.Player import Player

    player = Player(request.body)
    player.save()
    return response(player)

@post("/api/athletes/{id}")
async def post_athletes_id(request, response):
    from ..orm.Player import Player
    player = Player(request.body)
    if player.save():
        return response("Player saved")
    else:
        return response("Failed to save player!")

@post("/api/athletes/{id}/links")
async def post_athlete_links(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia(request.body)
    player_media.player_id = request.params["id"]
    if player_media.save():
        return response("Player Media saved")
    else:
        return response("Failed to save media!")

@delete("/api/athletes/{id}")
async def delete_athlete(request, response):
    from ..orm.Player import Player
    player = Player({"id": request.params["id"]})
    if player.delete():
        return response("Player deleted")
    else:
        return response("Failed to delete player!")

@delete("/api/athletes/{id}/links/{link_id}")
async def delete_athlete_link(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["link_id"]})
    if player_media.delete():
        return response("Player Media deleted")
    else:
        return response("Failed to delete media!")


@get("/api/athletes/{id}/transcripts/{media_id}/classification")
async def get_test_classification(request, response):
    from ..app.Scraper import aatos, classification_text
    from ..orm.PlayerTranscripts import PlayerTranscripts
    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and player_media_id = ?', params=[request.params["id"], request.params["media_id"]])
    transcript = player_transcripts.to_list(decode_transcript)[0]

    html = """<ul class='text-maastricht-blue'>
<li>A. Leadership and Teamwork </li>
<li>B. Resilience and Stress Management </li>
<li>C. Goal-Setting and Motivation </li>
<li>D. Communication Style </li>
<li>E. Problem-Solving and Critical Thinking </li>
<li>F. Adaptability and Flexibility </li>
<li>G. Self-Awareness and Reflection </li>
<li>H. Personal Relationships: Family and Friends </li>
<li>I. Unknown </li>
</ul>
\n"""

    text = ""
    for speaker in transcript["data"]["transcription"][0]:

        if speaker["speaker"] == transcript["selected_speaker"]:


                result = aatos.generate("Classify this text based on the CLASSIFICATION RULES into one or more categories:\nText:"+speaker["text"]+"\nUse the following output format for each line:\nClassification:[One or more classification categories]\nComment:[Short motivation for the classification]\n",
                                        "Human", "AI",
                                        "You are an AI assistant sports psychologist evaluating a list of phrases someone has said, use the CLASSIFICATION RULES to answer the question.",
                                        _context="CLASSIFICATION RULES:\n"+classification_text)

                html += """
                <div class="card">
                  <h5 class="card-header text-maastricht-blue">"""+speaker["text"]+"""</h5>
                  <div class="card-body">
                    <p class="card-text">"""+result["output"].replace("[", "").replace("]", "").replace("Comment:", "<br><b class='text-maastricht-blue'>Comment:</b>").replace("Classification:", "<b class='text-maastricht-blue'>Classification:</b>")+"""</p>
                  </div>
                </div><br>
                """



    return response(html)
