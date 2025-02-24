import ast
import json
from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_HTML, TEXT_PLAIN, HTTP_OK
from tina4_python.Template import Template
from tina4_python.Router import get, post, delete
import base64

from ..app.Scraper import get_youtube_videos, chunk_text
from ..app.Utility import get_data_tables_filter
from ..app.Player import get_player_results, submit_player_results
from .. import dba


@get("/api/athletes")
async def get_athletes(request, response):
    """
    Gets all the athletes
    :param request:
    :param response:
    :return:
    """
    if "draw" not in request.params:
        return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

    from ..orm.Player import Player

    data_tables_filter = get_data_tables_filter(request)

    where = "id <> ?"
    if data_tables_filter["where"] != "":
        where += " and " + data_tables_filter["where"]

    players = Player().select(["id", "first_name", "last_name", "date_of_birth", "sport", "home_town", "major"],
                              where,
                              [0],
                              order_by=data_tables_filter["order_by"],
                              limit=data_tables_filter["length"],
                              skip=data_tables_filter["start"], )

    data = players.to_paginate()

    data["draw"] = request.params["draw"]

    return response(data)


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

    if transcript:
        try:
            record["transcript"] = ast.literal_eval(base64.b64decode(transcript["data"]).decode("utf-8"))
        except Exception as e:
            record["transcript"] = str(e)
    else:
        record["transcript"] = None

    return record


def decode_transcript(record):
    try:
        record["data"] = ast.literal_eval(base64.b64decode(record["data"]).decode("utf-8"))
    except Exception as e:
        record["data"] = str(e)
    return record


@get("/api/athletes/{id}")
async def get_athlete(request, response):
    """
    :param request:
    :param response:
    :return:
    """
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia

    videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video-%' and is_deleted = 0 ",
                                  params=[request.params["id"]])
    player = Player({"id": request.params["id"]})

    if player.load():
        html = Template.render("player/profile.twig",
                               {"player": player.to_dict(), "videos": videos.to_list(decode_metadata)})
        return response(html)
    else:
        return response("Player error, or player not found")


@get("/api/athletes/{id}/results")
async def get_athlete_results(request, response):
    """
    Get athlete results
    :param request:
    :param response:
    :return:
    """
    from ..orm.Player import Player
    from ..orm.PlayerTranscripts import PlayerTranscripts
    player = Player({"id": request.params["id"]})
    player.load()

    player_transcripts = PlayerTranscripts().select("*", 'player_id = ?',
                                                    params=[request.params["id"]])

    text = ""
    transcripts = player_transcripts.to_list(decode_transcript)
    for transcript in transcripts:
        for speaker in transcript["data"]["transcription"]:
            if speaker["speaker"] == transcript["selected_speaker"]:
                text += speaker["text"]

    if str(player.candidate_id) != "":
        results = get_player_results(str(player.candidate_id))
    else:
        results = {"player": {"html": ""}, "coach": {"html": ""}, "scout": {"html": ""}}

    html = Template.render_twig_template("player/player-q-results.twig", {"player": player.to_dict(), "results": {"player": results["player"]["html"], "coach": results["coach"]["html"], "scout": results["scout"]["html"]}, "text": text})

    return response(html)

@post("/api/athletes/{id}/results")
async def post_athlete_results(request, response):
    """
    Update
    :param request:
    :param response:
    :return:
    """
    from ..orm.Player import Player
    player = Player({"id": request.params["id"]})
    player.load()

    results = submit_player_results(str(player.first_name), str(player.last_name), request.body["playerText"], str(player.candidate_id))

    if "candidate_id" in results:
        player.candidate_id = results["candidate_id"]
        player.save()

    return response.redirect("/api/athletes/"+request.params["id"]+"/results")


@get("/api/athletes/{id}/videos")
async def get_athlete_videos(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia

    player = Player({"id": request.params["id"]})
    player.load()

    if "search" in request.params and request.params["search"] == "1":
        you_tube_links = get_youtube_videos(str(player.first_name) + " " + str(player.last_name))
        for you_tube_link in you_tube_links:
            player_media = PlayerMedia()
            player_media.url = you_tube_link["url"]
            player_media.player_id = player.id
            player_media.media_type = 'video-youtube'
            player_media.is_valid = 1
            player_media.metadata = you_tube_link["metadata"]
            player_media.save()

    videos = PlayerMedia().select(limit=1, skip=0, filter="media_type like 'video%' and is_deleted = 0 and is_sorted = 0 and player_id = ?", params=[request.params["id"]])

    if videos.count > 0:
        video = videos.to_list(decode_metadata)[0]
        html = Template.render_twig_template("player/sorter.twig", {"video": video, "player": player.to_dict()})

    else:
        videos = PlayerMedia().select(limit=1000, filter="player_id = ? and media_type like 'video%' and is_deleted = 0 ",
                                      params=[request.params["id"]])

        html = Template.render("player/videos.twig",
                               {"videos": videos.to_list(decode_metadata), "player": player.to_dict()})
    return response(html)

@post("/api/athletes/{id}/videos")
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

    return response.redirect("/api/athletes/"+request.params["id"]+"/videos")

@get("/api/athletes/{id}/videos/{video_id}/transcript")
async def get_athlete_transcripts(request, response):
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


@post("/api/athletes/{id}/videos/{video_id}/transcript/queue")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.Queue import Queue
    queue = Queue()

    if not queue.load("player_media_id = ? ", [request.params["video_id"]]):
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
        where += " and " + data_tables_filter["where"]

    player_media = PlayerMedia().select(["id", "url", "media_type", "player_id", "is_valid", "date_created"],
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
    from ..app.Scraper import get_player_bio_urls

    player = Player(request.body)
    player.save()

    # add to queue
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
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.PlayerTranscripts import PlayerTranscripts

    player = Player({"id": request.params["id"]})
    if player.delete():
        player_medias = PlayerMedia().select("*", 'player_id = ?', params=[request.params["id"]])
        for player_media in player_medias.to_array():
            player_media = PlayerMedia({"id": player_media["id"]})
            player_media.delete()

        player_transcripts = PlayerTranscripts().select("*", 'player_id = ?')
        for player_transcript in player_transcripts.to_array():
            player_transcript = PlayerTranscripts({"id": player_transcript["id"]})
            player_transcript.delete()

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
    from ..orm.PlayerMedia import PlayerMedia
    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and player_media_id = ?',
                                                    params=[request.params["id"], request.params["media_id"]])
    transcript = player_transcripts.to_list(decode_transcript)[0]

    if "selected_speaker" in request.params:
        selected_speaker = request.params["selected_speaker"]
    else:
        selected_speaker = transcript["selected_speaker"]

    text = ""
    counter = 1
    for speaker in transcript["data"]["transcription"]:
        if speaker["speaker"] == selected_speaker:
            text += str(counter)+"."+ speaker["text"] + "\n\n"
            counter += 1

    #print("<pre style='width:200px'>",text, "<pre>")

    player_media = PlayerMedia({"id": request.params["media_id"]})
    classification = ""
    if player_media.load():
        if str(player_media.classification) == "" or ("refresh" in request.params and request.params["refresh"] == "1"):

            chunks = chunk_text(text, 5000)
            for chunk in chunks:
                result = aatos.generate("Classify each line of numbered text using the CLASSIFICATION RULES:\nText:"+chunk+"\nUse ONLY the following output format for each classification in the text:\nText:[Text being classified]\nClassification:[One or more classification categories comma separated]\nComment:[Short motivation for the classification of the text][LINE_FEED]\n",
                                                             "Human", "AI",
                                                             "You are an AI assistant sports psychologist evaluating a list of phrases someone has said, use the CLASSIFICATION RULES to answer the question.",
                                                            _context="CLASSIFICATION RULES:\n"+classification_text,
                                        _stop_tokens=["Human:"])

                classification += result["output"]

            dba.execute("update player_transcripts set selected_speaker = ? where id = ?", [selected_speaker,  transcript["id"]])
            dba.commit()

            player_media.classification = classification
            player_media.save()
        else:
            classification = str(player_media.classification.value)

        classification = "<div>"+classification.replace("\n", "</div><div>")+"</div>"
        classification = classification.replace("Text:", "")

    classification = """<div class="row"><div class="col"><ul class='text-maastricht-blue' style="position: sticky; top: 0">
        <li>A. Leadership and Teamwork </li>
        <li>B. Resilience and Stress Management </li>
        <li>C. Goal-Setting and Motivation </li>
        <li>D. Communication Style </li>
        <li>E. Problem-Solving and Critical Thinking </li>
        <li>F. Adaptability and Flexibility </li>
        <li>G. Self-Awareness and Reflection </li>
        <li>H. Personal Relationships: Family and Friends </li>
        <li>I. Unknown </li>
        </ul></div><div class="col">
        \n"""+classification+"</div>"

    return response(classification)

