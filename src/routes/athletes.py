import ast
import json
import base64
import hashlib
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from tina4_python import Debug
from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_HTML, TEXT_PLAIN, HTTP_OK, HTTP_NOT_FOUND
from tina4_python.Template import Template
from tina4_python.Router import get, post, delete
import re
from ..app.Scraper import get_youtube_videos, chunk_text
from ..app.Utility import get_data_tables_filter
from ..app.Player import get_player_results, submit_player_results, resize_profile_image, submit_player_teamq_details
from .. import dba

@get("/api/athletes/{status}")
async def get_athletes(request, response):
    """
    Gets all the athletes for the data grid
    :param request:
    :param response:
    :return:
    """
    if "draw" not in request.params:
        return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

    from ..orm.Player import Player
    from ..orm.Sport import Sport
    from ..app.Player import player_bio_complete, player_report_sent

    data_tables_filter = get_data_tables_filter(request)

    where = "id <> 0"
    if data_tables_filter["where"] != "":
        where += " and " + data_tables_filter["where"]

    if request.params["status"] != "all":
        if request.params["status"] == "unsent-reports":
            where += " and id not in (select player_id from player_result)"
        if request.params["status"] == "completed-reports":
            where += " and id in (select player_id from player_result)"
        if request.params["status"] == "unverified-speakers":
            where += (" and id in (select pt.player_id from player_transcripts pt "
                      "join player_media pm "
                      "on pt.player_id = pm.player_id "
                      "and pt.verified_user_id = 0 "
                      "and pm.is_sorted = 1 "
                      "AND pm.is_valid = 1 "
                      "AND pm.media_type = 'video-youtube' "
                      "group by pt.player_id)")
        if request.params["status"] == "verified-speakers":
            where += (" and id in (SELECT pt.player_id FROM player_transcripts pt "
                      "JOIN player_media pm "
                      "ON pt.player_id = pm.player_id "
                      "AND pt.verified_user_id > 0 "
                      "AND pm.is_valid = 1 "
                      "AND pm.media_type = 'video-youtube' "
                      "GROUP BY pt.player_id HAVING COUNT(pt.id) = COUNT(pm.id))")
        if request.params["status"] == "unverified-videos":
            where += " and id in (select player_id from player_media where is_valid = 0 and is_deleted = 0)"
        if request.params["status"] == "verified-videos":
            where += " and id in (select player_id from player_media where is_valid = 1 and is_deleted = 0)"
        if request.params["status"] == "incomplete-bios":
            where += " and (image is null or first_name = '' or last_name = '' or sport = '' or position = '' or date_of_birth is null or home_town = '' or team = '')"

    if "selectedSport" in request.params and request.params["selectedSport"] != "":
        where += f" and sport = '{request.params["selectedSport"]}'"

    players = Player().select(["id", "first_name", "last_name", "date_of_birth", "sport", "home_town", "major"],
                              where,
                              order_by=data_tables_filter["order_by"],
                              limit=data_tables_filter["length"],
                              skip=data_tables_filter["start"], )
    if players.count == 0:
        return response('{"error": "No matching players found"}', HTTP_NOT_FOUND, TEXT_PLAIN)

    data = players.to_paginate()

    data["draw"] = request.params["draw"]

    # loop through the players and get the transcribe stats
    for player in data["data"]:
        player["transcript_stats"] = player_transcript_stats(player["id"])
        player["completed_bio"] = player_bio_complete(player["id"])
        player["report_sent"] = player_report_sent(player["id"])
        # Return only the date, Y-m-d format
        player["date_of_birth"] = player["date_of_birth"].split("T")[0]

    return response(data)

def player_transcript_stats(player_id):
    """
    Get the player transcript and media stats
    :param player_id:
    :return:
    """
    from ..app.Queue import get_player_transcribed_stats

    player_transcripts = get_player_transcribed_stats(player_id)

    return player_transcripts

def decode_metadata(record):
    """
    Decode Metadata
    :param record:
    :return:
    """

    try:
        record["metadata"] = json.loads(record["metadata"])
    except Exception as e:
        record["metadata"] = ast.literal_eval(record["metadata"])

    record["title"] = record["metadata"]["items"][0]["snippet"]["title"]
    record["description"] = record["metadata"]["items"][0]["snippet"]["description"]
    record["published_at"] = record["metadata"]["items"][0]["snippet"]["publishedAt"]

    transcript = dba.fetch_one("select * from player_transcripts where player_media_id = ?", [record["id"]])
    record["transcript_verified"] = False
    record["transcript"] = None

    if transcript:
        try:
            record["transcript"] = ast.literal_eval(base64.b64decode(transcript["data"]).decode("utf-8"))
            record["transcript_verified"] = transcript["verified_user_id"] > 0
        except Exception as e:
            record["transcript"] = str(e)

    return record

def decode_player_image(record):
    try:
        record["image"] = ast.literal_eval(base64.b64decode(record["image"]).decode("utf-8"))
    except Exception as e:
        record["image"] = str(e)
    return record

@get("/api/receptiviti/export")
async def get_receptiviti_export(request, response):
    from ..app.Player import decode_transcript
    from ..orm.PlayerTranscripts import PlayerTranscripts

    file_name = "transcript_export.csv"

    headers = {
        "Content-Disposition": f"attachment; filename={file_name}",
        "Content-Type": "text/csv"
    }

    player_transcripts = PlayerTranscripts().select("t.*, (select candidate_id from player where id = t.player_id) as candidate_id", 'verified_user_id > 0 and exists (select id from player_media where id = t.player_media_id and is_valid = 1)', limit=100000000, order_by="player_id")
    text = "\"player_id\",\"candidate_id\",\"text\"\n"
    transcripts = player_transcripts.to_list(decode_transcript)
    player_id = ""
    for transcript in transcripts:
        if player_id != transcript["player_id"]:
            if player_id != "":
                text += "\"\n"
            if transcript["candidate_id"] == "":
                transcript["candidate_id"] = "NA"
            text += str(transcript["player_id"])+",\""+str(transcript["candidate_id"])+"\",\""
            player_id = transcript["player_id"]

        for speaker in transcript["data"]["transcription"]:
            if speaker and "speaker" in speaker:
                if speaker["speaker"] == transcript["selected_speaker"]:
                    text += speaker["text"].replace("\n", "").replace("\"", "")
    # last line needs to be closed
    text += "\"\n"

    return response(text, 200, "text/csv", headers_in=headers)



@get("/athlete/{id}")
async def get_athlete(request, response):
    """
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Sport import Sport

    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video-%' and is_deleted = 0 ",
                                  params=[request.params["id"]])
    player = Player({"id": request.params["id"]})

    if player.load():
        if player.image.value is not None:
            raw_value = str(player.image.value)
            player_image = base64.b64decode(raw_value).decode("utf-8")
        else:
            player_image = "None"

        sports = Sport().select('*', limit=100).to_list()

        html = Template.render("player/profile.twig",
                               {"player": player.to_dict(),  "player_image": player_image,
                                "videos": videos.to_list(decode_metadata), "sports": sports})
        return response(html)
    else:
        return response("Player error, or player not found")

@get("/api/athlete/{id}/sport-positions/{sport_name}")
async def get_athlete_sport_position_select(request, response):
    """
    Get the sport positions for the athlete
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    from ..orm.Sport import Sport
    from ..orm.SportPosition import SportPosition
    from ..orm.Player import Player
    from urllib.parse import unquote

    player = Player({"id": request.params["id"]})
    player.load()
    player = player.to_dict()

    # url decode sport_name param
    sport_name = unquote(request.params["sport_name"])

    sport = Sport().select('*', "name = ?", params=[sport_name], limit=1).to_list()
    if len(sport) == 0:
        return response("Sport not found", HTTP_NOT_FOUND, TEXT_PLAIN)

    sport_positions = SportPosition().select("*", "sport_id = ?", params=[sport[0]["id"]], limit=100)
    selected_position = player["position"]

    if sport_positions.count == 0:
        return response("No positions found for this sport", HTTP_NOT_FOUND, TEXT_PLAIN)

    html = Template.render_twig_template("components/position_select.twig", {"positions": sport_positions.to_list(), "selected_position": selected_position})

    return response(html)

@get("/api/athlete/{id}/report")
async def get_athlete_full_report(request, response):
    from ..orm.Player import Player
    player = Player({"id": request.params["id"]})
    player.load()

    if player.image.value is not None:
        player_image = base64.b64decode(player.image.value).decode("utf-8")
    else:
        player_image = "None"

    if str(player.candidate_id) != "":
        results = get_player_results(str(player.candidate_id))
    else:
        results = {"full_report": {"pages": []}}

    if "candidate_id" in results and results["candidate_id"] != "":
        candidate_id = results["candidate_id"]
    else:
        candidate_id = player.candidate_id

    html = Template.render_twig_template("player/reports/full_report.twig", {
        "url": os.getenv("TEAMQ_ENDPOINT"),
        "candidate_id": candidate_id,
        "player": player.to_dict(),
        "player_image": player_image,
        "full_report": results["full_report"],
        "current_date": datetime.now().strftime("%m/%d/%Y %H:%M")
    })

    return response(html)

@get("/api/athlete/{id}/report/{report_type}")
async def get_athlete_report(request, response):
    from ..orm.Player import Player
    player = Player({"id": request.params["id"]})
    report_type = request.params["report_type"]
    player.load()

    if player.image.value is not None:
        player_image = base64.b64decode(player.image.value).decode("utf-8")
    else:
        player_image = "None"

    if str(player.candidate_id) != "":
        results = get_player_results(str(player.candidate_id))
    else:
        results = {"full_report": {"pages": []}}

    report = []

    for page in results["full_report"]["pages"]:
        if page["category"] == report_type:
            report.append(page)

    if "candidate_id" in results and results["candidate_id"] != "":
        candidate_id = results["candidate_id"]
    else:
        candidate_id = player.candidate_id

    html = Template.render_twig_template("player/reports/report.twig", {
        "url": os.getenv("TEAMQ_ENDPOINT"),
        "candidate_id": candidate_id,
        "player": player.to_dict(),
        "player_image": player_image,
        "report": report,
        "current_date": datetime.now().strftime("%m/%d/%Y %H:%M")
    })

    return response(html)

@get("/api/athlete/{id}/results")
async def get_athlete_results(request, response):
    """
    Get athlete results
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    from ..app.Player import decode_transcript
    from ..orm.Player import Player
    from ..orm.PlayerTranscripts import PlayerTranscripts
    from ..orm.PlayerResult import PlayerResult
    player = Player({"id": request.params["id"]})
    player.load()

    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and verified_user_id > 0 and exists (select id from player_media where id = t.player_media_id and is_valid = 1) ',
                                                    params=[request.params["id"]])
    text = ""
    results = {"player": {"html": ""}, "coach": {"html": ""}, "scout": {"html": ""}}

    player_result = PlayerResult().select("data, player_id, transcription", "player_id = ?", params=[str(player.id)], order_by=["date_created desc"], limit=1)
    if player_result:
        player_result = player_result.to_list()
        if len(player_result) == 1:
            results = json.loads(base64.b64decode(str(player_result[0]["data"])).decode("utf-8"))

    if text == "":
        transcripts = player_transcripts.to_list(decode_transcript)
        for transcript in transcripts:
            for speaker in transcript["data"]["transcription"]:
                if speaker and "speaker" in speaker:
                    if speaker["speaker"] == transcript["selected_speaker"]:
                        text += speaker["text"]

        if str(player.candidate_id) != "":
                results = get_player_results(str(player.candidate_id))

    # remove any none latin characters from text
    text = ''.join([i if ord(i) < 128 else '' for i in text])

    if "candidate_id" in results and results["candidate_id"] != "":
        candidate_id = results["candidate_id"]
    else:
        candidate_id = player.candidate_id

    html = Template.render_twig_template("player/player-q-results.twig", {
        "url": os.getenv("TEAMQ_ENDPOINT"),
        "candidate_id": candidate_id,
        "player": player.to_dict(),
        "results": {
            "player": results["player"]["html"],
            "coach": results["coach"]["html"],
            "scout": results["scout"]["html"]
        },
        "text": text
    })

    return response(html)

@post("/api/athlete/{id}/upload-picture")
async def post_upload_picture(request, response):
    from ..orm.Player import Player
    player = Player({"id": request.params["id"]})
    player.load()

    try:
        player.image = str(resize_profile_image(request.body["picture-upload"]["content"]))
    except Exception as e:
        return response(str(e))

    player.save()
    return response("<script>loadPage('/api/athlete/"+request.params["id"]+"', 'content')</script>")

@post("/api/athlete/{id}/results")
async def post_athlete_results(request, response):
    """
    Update
    :param request:
    :param response:
    :return:
    """

    from ..orm.PlayerResult import PlayerResult
    from ..app.Player import split_trim_minify

    # create hash of the playerText
    player_text: str = str(request.body["playerText"])
    transcription_hash = hashlib.md5(player_text.encode("utf-8")).hexdigest()
    player_result = PlayerResult().select("*", "transcript_hash = ?", params=[transcription_hash])
    player_result = player_result.to_list()
    if len(player_result) > 0:
        return response.redirect("/api/athlete/"+request.params["id"]+"/results")

    from ..orm.Player import Player
    player = Player({"id": request.params["id"]})
    player.load()
    if player.image:
        player.image = base64.b64decode(player.image.value).decode("utf-8")
    else:
        player.image = ""

    results = submit_player_results(
        str(player.first_name),
        str(player.last_name),
        str(player.image),
        request.body["playerText"],
        str(player.candidate_id),
        str(player.sport),
        str(player.position),
        str(player.date_of_birth),
        str(player.home_town),
        str(player.team)
    )

    if "candidate_id" in results:
        player.candidate_id = results["candidate_id"]
        player.save()

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


    player_result = PlayerResult({
        "player_id": request.params["id"],
        "transcript_hash": transcription_hash,
        "transcription": request.body["playerText"],
        "data": json.dumps({"player": results["player"], "coach": results["coach"], "scout": results["scout"]})
    })

    player_result.save()

    return response.redirect("/api/athlete/"+request.params["id"]+"/results")


@get("/api/athlete/{id}/videos")
async def get_athlete_videos(request, response):
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia

    player = Player({"id": request.params["id"]})
    player.load()

    if "search" in request.params and request.params["search"] == "1":
        video_sport_search_criteria = str(player.sport)
        if player.sport == "American Football":
            video_sport_search_criteria = "NFL, American Football"
        if player.sport == "EU Football/ Soccer":
            video_sport_search_criteria = "Soccer, European Union Football"

        you_tube_links = get_youtube_videos(str(player.first_name) + " " + str(player.last_name), video_sport_search_criteria)
        for you_tube_link in you_tube_links:
            player_media = PlayerMedia()
            player_media.url = you_tube_link["url"]
            player_media.player_id = player.id
            player_media.media_type = 'video-youtube'
            player_media.is_valid = 1
            player_media.metadata = you_tube_link["metadata"]
            player_media.save()

    all_videos = PlayerMedia().select(skip=0, filter="media_type like 'video%' and is_deleted = 0 and is_valid = 1 and player_id = ?", params=[request.params["id"]], limit=200)

    unsorted_videos = PlayerMedia().select(skip=0, filter="media_type like 'video%' and is_deleted = 0 and is_valid = 1 and is_sorted = 0 and player_id = ?", params=[request.params["id"]])
    if unsorted_videos.count > 0:
        video = unsorted_videos.to_list(decode_metadata)[0]
        videos_processed = PlayerMedia().select("count(*) as count", limit="1", filter="player_id = ? and media_type like 'video%' and is_deleted = 0 and is_valid = 1 and is_sorted = 1", params=[request.params["id"]])
        html = Template.render_twig_template("player/sorter.twig", {"remaining_videos": all_videos.count, "videos_processed": videos_processed.to_list()[0]['count'], "video": video, "player": player.to_dict()})

    else:
        videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video%' and is_deleted = 0 ",
                                      params=[request.params["id"]])

        html = Template.render("player/videos.twig",
                               {"videos": videos.to_list(decode_metadata), "player": player.to_dict()})
    return response(html)


@post("/api/athlete/{id}/videos")
async def post_athlete_videos(request, response):
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Queue import Queue

    player_media = PlayerMedia({"id": request.body["player_media_id"]})
    player_media.load()

    if request.body["is_valid"] == "1":
        player_media.is_valid  = 1

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

    return response.redirect("/api/athlete/"+request.params["id"]+"/videos")

@get("/api/athlete/{id}/videos/{video_id}/transcript")
async def get_athlete_transcripts(request, response):
    from ..app.Player import decode_transcript
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.PlayerTranscripts import PlayerTranscripts
    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and id = ? and is_deleted = 0 ",
                                  params=[request.params["id"], request.params["video_id"]])
    player = Player({"id": request.params["id"]})
    player.load()

    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and player_media_id = ?',
                                                    params=[request.params["id"], request.params["video_id"]])

    if videos.count > 0:
        video = videos.to_list(decode_metadata)[0]
    else:
        video = None

    if player_transcripts.count > 0:
        player_transcripts = player_transcripts.to_list(
            decode_transcript)
    else:
        player_transcripts = None

    html = Template.render("player/video-transcript.twig", {"player": player.to_dict(), "video": video,
                                                            "transcripts": player_transcripts})
    return response(html)


@post("/api/athlete/{id}/videos/{video_id}/transcript/queue")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.Queue import Queue
    queue = Queue()

    if not queue.load("player_media_id = ? ", [request.params["video_id"]]):
        queue.action = 'transcribe'
        queue.player_id = request.params["id"]
        queue.data = {"player_media_id": request.params["video_id"]}
        queue.save()
    return response("Queued!")


@post("/api/athlete/{id}/videos/{video_id}/remove")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["video_id"]})
    if player_media.load():
        player_media.is_deleted = 1
        player_media.save()

    return response("Removed!")


@post("/api/athlete/{id}/videos/{video_id}/include")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["video_id"]})
    if player_media.load():
        if player_media.is_valid.value:
            player_media.is_valid = 0
        else:
            player_media.is_valid = 1

        player_media.save()

    return response("Done!")


@get("/api/athlete/{id}/links")
async def get_athlete_links(request, response):
    """
    Route to return the links template.
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    data = {
        "player_id": request.params["id"]
    }

    return response(Template.render_twig_template("player/links.twig", data))

@get("/api/athlete/{id}/links_data")
async def get_athlete_links_data(request, response):
    if "draw" not in request.params:
        return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

    from ..orm.PlayerMedia import PlayerMedia

    data_tables_filter = get_data_tables_filter(request)

    where = "id <> ? and player_id = ?"
    if data_tables_filter["where"] != "":
        where += " and " + data_tables_filter["where"]

    player_media = PlayerMedia().select(["id", "url", "media_type", "player_id", "is_valid", "date_created", "is_deleted", "is_sorted"],
                                        where,
                                        [0, request.params["id"]],
                                        order_by=data_tables_filter["order_by"],
                                        limit=data_tables_filter["length"],
                                        skip=data_tables_filter["start"], )

    data = player_media.to_paginate()

    data["draw"] = request.params["draw"]

    return response(data)


@post("/api/athletes")
async def post_athletes(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Sport import Sport
    from ..orm.AdminSetting import AdminSetting
    from ..app.Scraper import get_player_bio_urls

    player = Player(request.body)
    player.save()

    # add to queue
    bio_urls = get_player_bio_urls(str(player.first_name) + " " + str(player.last_name), player.sport)

    for url in bio_urls:
        player_media = PlayerMedia({"url": url, "media_type": "link-bio", "player_id": player.id})

        if player_media.load("url = ? and player_id = ? and media_type = 'link-bio'", [url, player.id]):
            # exists
            pass
        else:
            player_media.is_valid = 1

        player_media.save()

    setting_query = "setting_key = 'video_sport_search_parameters'"
    if player.sport:
        sport = Sport().select("*", "name = ?", params=[str(player.sport)], limit=1)
        if sport.count > 0:
            setting_query = f"setting_key = 'video_sport_{sport[0]["id"]}_search_parameters'"

    search_query_setting = AdminSetting().select("*", setting_query, limit=1)
    video_sport_search_criteria = str(player.sport)
    if search_query_setting.count > 0:
        video_sport_search_criteria = search_query_setting[0]["setting_value"]

    you_tube_links = get_youtube_videos(str(player.first_name) + " " + str(player.last_name), video_sport_search_criteria)
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

    return response(player)


@post("/api/athlete/{id}")
async def post_athletes_id(request, response):
    from ..orm.Player import Player
    player_params = request.body
    # get the player image from the database
    player = Player({"id": player_params["id"]})
    player.load()

    if player.image:
        player.image = base64.b64decode(player.image.value).decode("utf-8")
    else:
        player.image = ""

    player_params["image"] = player.image

    if player.candidate_id:
        player_params["candidate_id"] = str(player.candidate_id)

    player = Player(player_params)
    if player.save():
        teamq_updated = submit_player_teamq_details(player)

        return response(f"Player saved. {'TeamQ updated.' if teamq_updated["error"] is None else teamq_updated['error']}", HTTP_OK, TEXT_PLAIN)
    else:
        return response("Failed to save player!")


@post("/api/athlete/{id}/links")
async def post_athlete_links(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia(request.body)
    player_media.player_id = request.params["id"]

    if request.body["mediaType"] == "video-youtube":
        from ..app.Scraper import get_youtube_info
        # strip out the video id from the url "?v=" param
        parsed_url = urlparse(request.body["url"])
        params = parse_qs(parsed_url.query)
        if params.get("v"):
            video_id = params.get("v")[0]
            video_meta = get_youtube_info(video_id)
            if video_meta:
                player_media.is_valid = 1
                player_media.metadata = video_meta

    if player_media.save():
        return response("Player Media saved")
    else:
        return response("Failed to save media!")


@delete("/api/athlete/{id}")
async def delete_athlete(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.PlayerTranscripts import PlayerTranscripts

    player = Player({"id": request.params["id"]})
    if player.delete():
        player_medias = PlayerMedia().select("*", 'player_id = ?',
                                             params=[request.params["id"]])

        for player_media in player_medias.to_array():
            player_media = PlayerMedia({"id": player_media["id"]})
            player_media.delete()

        player_transcripts = PlayerTranscripts().select("*", 'player_id = ?',
                                                        params=[request.params["id"]])
        for player_transcript in player_transcripts.to_array():
            player_transcript = PlayerTranscripts({"id": player_transcript["id"]})
            player_transcript.delete()

        return response("Player, media and transcripts deleted")

    return response("Failed to delete player!")


@delete("/api/athlete/{id}/links/{link_id}")
async def delete_athlete_link(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["link_id"]})
    if player_media.delete():
        return response("Player Media deleted")
    else:
        return response("Failed to delete media!")

@post("/api/athlete/{id}/links/{link_id}/restore")
async def post_athlete_link_restore(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["link_id"]})
    if player_media.load():
        player_media.is_deleted = 0
        player_media.save()
        return response("Player Media restored")
    else:
        return response("Failed to restore media!")


@get("/api/athlete/{id}/transcripts/{media_id}/classification")
async def get_test_classification(request, response):
    from ..app.Player import decode_transcript
    from ..app.Scraper import aatos, classification_text
    from ..orm.PlayerTranscripts import PlayerTranscripts
    from ..orm.PlayerMedia import PlayerMedia
    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and player_media_id = ?',
                                                    params=[request.params["id"], request.params["media_id"]])
    transcript = player_transcripts.to_list(decode_transcript)[0]

    if "data" not in transcript and "transcription" not in transcript["data"] and len(transcript["data"]["transcription"]) == 0:
        return response("No data yet.")

    if "selected_speaker" in request.params:
        selected_speaker = request.params["selected_speaker"]
        # update the selected speaker in the transcript
        player_transcript = PlayerTranscripts({"id": transcript["id"]})
        player_transcript.load()
        if type(player_transcript.data.value) is str:
            player_transcript.data = ast.literal_eval(base64.b64decode(player_transcript.data.value).decode("utf-8"))
        player_transcript.selected_speaker = selected_speaker
        player_transcript.save()
    else:
        selected_speaker = transcript["selected_speaker"]

    text = ""
    counter = 1
    for speaker in transcript["data"]["transcription"]:
        if speaker["speaker"] == selected_speaker:
            speaker_text = ''.join([i if ord(i) < 128 else ' ' for i in speaker["text"]])
            text += str(counter)+"."+ speaker_text + "\n\n"
            counter += 1

    #print("<pre style='width:200px'>",text, "<pre>")

    player_media = PlayerMedia({"id": request.params["media_id"]})
    classification = ""
    if player_media.load():
        if str(player_media.classification) == "" or ("refresh" in request.params and request.params["refresh"] == "1"):

            chunks = chunk_text(text, 5000)
            for chunk in chunks:
                try:
                    result = aatos.generate("Classify each line of numbered text using the CLASSIFICATION RULES:\nText:"+chunk+"\nUse ONLY the following output format for each classification in the text:\nText:[Text being classified]\nClassification:[One or more classification categories comma separated]\nComment:[Short motivation for the classification of the text][LINE_FEED]\n",
                                                                 "Human", "AI",
                                                                 "You are an AI assistant sports psychologist evaluating a list of phrases someone has said, use the CLASSIFICATION RULES to answer the question.",
                                                                _context="CLASSIFICATION RULES:\n"+classification_text,
                                            _stop_tokens=["Human:"])

                    classification += result["output"]
                except Exception as e:
                    print("Error in classification:", e)
                    return response("Could not classify text.")

            dba.execute("update player_transcripts set selected_speaker = ? where id = ?", [selected_speaker,  transcript["id"]])
            dba.commit()

            player_media.classification = classification
            player_media.save()
        else:
            classification = str(player_media.classification.value)

        classification = "<div>"+classification.replace("\n", "</div><div>")+"</div>"
        classification = classification.replace("Text:", "")

    classification = """<div class="row"><div class="col-12 col-xl-5"><ul class='text-black text-black pl-3' style="position: sticky; top: 0">
        <li>A. Leadership and Teamwork </li>
        <li>B. Resilience and Stress Management </li>
        <li>C. Goal-Setting and Motivation </li>
        <li>D. Communication Style </li>
        <li>E. Problem-Solving and Critical Thinking </li>
        <li>F. Adaptability and Flexibility </li>
        <li>G. Self-Awareness and Reflection </li>
        <li>H. Personal Relationships: Family and Friends </li>
        <li>I. Unknown </li>
        </ul></div><div class="col-12 col-xl-7">
        \n"""+classification+"</div>"

    return response(classification)

@post("/api/athlete/{id}/transcript/{transcript_id}/verified")
async def post_transcript_verified(request, response):
    """
    Sets the transcript as verified using the current logged-in user as the integer in the field
    :param request:
    :param response:
    :return:
    """
    from ..orm.PlayerTranscripts import PlayerTranscripts

    player_transcript = PlayerTranscripts({"id": request.params["transcript_id"]})
    player_transcript.load()
    if type(player_transcript.data.value) is str:
        player_transcript.data = ast.literal_eval(base64.b64decode(player_transcript.data.value).decode("utf-8"))
    player_transcript.verified_user_id = request.body["verified_user_id"]
    player_transcript.verified_at = datetime.now()
    player_transcript.save()

    return response("Done!")

@get("/athletes/athlete-template.csv")
async def get_athletes_csv_template(request, response):
    """
    Returns the csv template for importing athletes
    :param request:
    :param response:
    :return:
    """
    csv_template = "first_name,last_name,sport,position,team\n"
    return response(csv_template, 200, "text/csv", headers_in={"Content-Disposition": "attachment; filename=athlete_template.csv"})

@post("/api/athletes/import-csv")
async def post_import_csv(request, response):
    """
    Get the file upload from request and import the csv data
    :param request:
    :param response:
    :return:
    """
    from ..app.Player import import_csv_player_data

    if "importCsv" not in request.body:
        return response("No file found", HTTP_SERVER_ERROR, TEXT_PLAIN)

    # decode file contents
    file_content = base64.b64decode(request.body["importCsv"]["content"]).decode('utf-8')
    import_count = import_csv_player_data(str(file_content))

    if import_count > 0:
        return response("Imported "+str(import_count)+" players")
    Debug.error("No players imported")

    return response("No players imported", HTTP_SERVER_ERROR, TEXT_PLAIN)

@post("/api/athletes/request-results")
async def post_send_results(request, response):
    """
    Queue the players to request their Receptiviti results
    :param request:
    :param response:
    :return:
    """
    if request.body["playerIds"] == "":
        return response("No players selected", HTTP_SERVER_ERROR, TEXT_PLAIN)

    from ..app.QueueUtility import QueueUtility

    queue = QueueUtility()
    player_ids = json.loads(request.body["playerIds"])
    for player_id in player_ids:
        queue.add_item("request_player_results", {"player_id": player_id})

    return response("Done!")


@get('/athletes/fix-images')
async def get_fix_images(request, response):
    """
    Fix the images of the players
    :param request:
    :param response:
    :return:
    """
    from ..orm.Player import Player

    players = Player().select("*", "image is not null and image <> ''", limit=500)
    for player in players.to_array():
        player["image"] = base64.b64decode(player["image"]).decode("utf-8")
        # check if the image is a base64 string, do nothing
        if player["image"].startswith("b'") or player["image"].startswith("b\""):
            # remove the byte string
            player["image"] = player["image"][2:-1]

        if player["image"] != "":
            p = Player({"id": player["id"]})
            p.load()
            p.image = player["image"]
            p.save()

    return response("Done!")

@get('athletes/resend-deleted-videos')
async def get_resend_deleted_videos(request, response):
    """
    Resend deleted videos to the player
    :param request:
    :param response:
    :return:
    """
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Queue import Queue

    videos = PlayerMedia().select("id, player_id, CONCAT(('{\"player_media_id\": '), id, '}') as data", "player_id > 153 and is_valid = 1 and is_deleted = 1 and media_type like 'video-%'", limit=2000)
    counter = 0
    for video in videos.to_array():
        try:
            queue = Queue()
            queue.action = 'transcribe'
            queue.player_id = video["player_id"]
            queue.data = video["data"]
            queue.save()
        except Exception as e:
            Debug.error("Error resending video: "+str(e))
            continue

        queue = queue.to_dict()

        if queue["id"] > 0:
            player_media = PlayerMedia({"player_id": video["player_id"], "id": video["id"]})
            player_media.load()

            player_media.is_deleted = 0
            player_media.save()
            counter += 1

    return response(f"Done, sent {counter} videos!")

@get('athletes/get-sports')
async def get_sports(request, response):
    """
    Get the sports from the TeamQ api
    :param request:
    :param response:
    :return:
    """
    from ..app.Setup import sync_sports_positions

    sync_sports_positions(dba)

    return response("Done!")