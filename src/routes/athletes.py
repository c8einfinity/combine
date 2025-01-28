import json
from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_HTML, TEXT_PLAIN, HTTP_OK
from tina4_python.Request import params
from tina4_python.Template import Template
from tina4_python.Router import get, post, delete
from tina4_python.Swagger import secure

from ..app.Setup import check_players
from ..app.Utility import get_data_tables_filter


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

    return record

def decode_transcript(record):
    record["data"] = json.loads(record["data"])
    return record


@get("/api/athletes/{id}")
async def get_athlete(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia

    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video%' ", params=[request.params["id"]])
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
    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video%' ", params=[request.params["id"]])
    player = Player({"id": request.params["id"]})
    html = Template.render("player/videos.twig", {"player": player.to_dict(), "videos": videos.to_list(decode_metadata)})
    return response(html)


@get("/api/athletes/{id}/videos/{video_id}/transcript")
async def get_athlete_transcripts(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.PlayerTranscripts import PlayerTranscripts
    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and id = ? ", params=[request.params["id"], request.params["video_id"]])
    player = Player({"id": request.params["id"]})
    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and player_media_id = ?', params=[request.params["id"], request.params["video_id"]])
    html = Template.render("player/video-transcript.twig", {"player": player.to_dict(), "video": videos.to_list(decode_metadata)[0], "transcripts": player_transcripts.to_list(decode_transcript)})
    return response(html)


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

@delete("/api/athletes/{id}/links/{link_id}")
async def delete_athlete_link(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["link_id"]})
    if player_media.delete():
        return response("Player Media deleted")
    else:
        return response("Failed to delete media!")

