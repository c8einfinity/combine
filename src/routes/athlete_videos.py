# Copyright 2025 Code Infinity
# Author: Jacques van Zuydam <jacques@codeinfinity.co.za>
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

import ast
import base64
import json
from datetime import datetime
from tina4_python.Constant import TEXT_HTML, HTTP_OK
from tina4_python.Template import Template
from tina4_python.Router import get, post, middleware
from ..app.Scraper import get_youtube_videos, chunk_text
from .. import dba
from ..app.MiddleWare import MiddleWare

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

@middleware(MiddleWare, ["after_route_session_validation"])
@get("/api/athlete/{id}/videos")
async def get_athlete_videos(request, response):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Sport import Sport
    from ..orm.AdminSetting import AdminSetting

    player = Player({"id": request.params["id"]})
    player.load()

    if "search" in request.params and request.params["search"] == "1":
        setting_query = "setting_key = 'video_sport_search_parameters'"
        if player.sport:
            sport = Sport().select("*", "name = ?", params=[str(player.sport)], limit=1)
            if sport.count > 0:
                setting_query = f"setting_key = 'video_sport_{sport[0]["id"]}_search_parameters'"

        search_query_setting = AdminSetting().select("*", setting_query, limit=1)
        video_sport_search_criteria = str(player.sport)
        if search_query_setting.count > 0:
            video_sport_search_criteria = search_query_setting[0]["setting_value"]

        you_tube_links = get_youtube_videos(str(player.first_name) + " " + str(player.last_name),
                                            video_sport_search_criteria)
        for you_tube_link in you_tube_links:
            player_media = PlayerMedia()
            # Check if the video already exists
            existing_media = PlayerMedia().select("id", "player_id = ? and url = ?",
                                                  params=[request.params["id"], you_tube_link["url"]], limit=1)

            if existing_media.count > 0:
                player_media.id = existing_media[0]["id"]
                player_media.load()

            player_media.url = you_tube_link["url"]
            player_media.player_id = player.id
            player_media.media_type = 'video-youtube'
            player_media.is_valid = 1
            player_media.metadata = you_tube_link["metadata"]
            player_media.save()

    all_videos = PlayerMedia().select(skip=0,
                                      filter="media_type like 'video%' and is_deleted = 0 and is_valid = 1 and player_id = ?",
                                      params=[request.params["id"]], limit=200)

    unsorted_videos = PlayerMedia().select(skip=0,
                                           filter="media_type like 'video%' and is_deleted = 0 and is_valid = 1 and is_sorted = 0 and player_id = ?",
                                           params=[request.params["id"]])
    if unsorted_videos.count > 0:
        video = unsorted_videos.to_list(decode_metadata)[0]
        videos_processed = PlayerMedia().select("count(*) as count", limit="1",
                                                filter="player_id = ? and media_type like 'video%' and is_deleted = 0 and is_valid = 1 and is_sorted = 1",
                                                params=[request.params["id"]])
        html = Template.render_twig_template("player/sorter.twig", {"remaining_videos": all_videos.count,
                                                                    "videos_processed": videos_processed.to_list()[0][
                                                                        'count'], "video": video,
                                                                    "player": player.to_dict()})

    else:
        videos = PlayerMedia().select(limit=1,
                                     filter="player_id = ? and is_deleted = 0 "
                                            "and media_type like 'video%' "
                                            "and not exists (select 1 from player_transcripts where player_media_id = t.id and verified_user_id > 0)",
                                     params=[request.params["id"]])
        if videos.count == 0:
            videos = PlayerMedia().select(limit=1,
                                           filter="player_id = ? and is_deleted = 0 "
                                                  "and media_type like 'video%' "
                                                  "and exists (select 1 from player_transcripts where player_media_id = t.id and verified_user_id > 0)",
                                           params=[request.params["id"]])

        html = Template.render("player/videos.twig",
                               {"videos": videos.to_list(decode_metadata), "player": player.to_dict()})

    dba.close()

    return response(html)

@middleware(MiddleWare, ["after_route_session_validation"])
@post("/api/athlete/{id}/videos")
async def post_athlete_videos(request, response):
    from ..orm.PlayerMedia import PlayerMedia
    from ..orm.Queue import Queue

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

    dba.close()

    return response.redirect("/api/athlete/" + request.params["id"] + "/videos")

@middleware(MiddleWare, ["after_route_session_validation"])
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

    dba.close()

    html = Template.render("player/video-transcript.twig", {"player": player.to_dict(), "video": video,
                                                            "transcripts": player_transcripts,"showClassification": False})
    return response(html)

@middleware(MiddleWare, ["after_route_session_validation"])
@get("/api/athlete/{id}/video-list")
async def get_athlete_video_list(request, response):
    from ..orm.PlayerMedia import PlayerMedia
    verified_videos = PlayerMedia().select(limit=1000,
                                           filter="player_id = ? and is_deleted = 0 "
                                                  "and media_type like 'video%' "
                                                  "and exists (select 1 from player_transcripts where player_media_id = t.id and verified_user_id > 0)",
                                  params=[request.params["id"]])

    unverified_videos = PlayerMedia().select(limit=1000,
                                           filter="player_id = ? and is_deleted = 0 "
                                                  "and media_type like 'video%' "
                                                  "and not exists (select 1 from player_transcripts where player_media_id = t.id and verified_user_id > 0)",
                                    params=[request.params["id"]])

    videos = unverified_videos.to_list(decode_metadata) + verified_videos.to_list(decode_metadata)

    if len(videos) > 0:
        if request.params["selectedvideoid"]:
            # remove the selected video from the list
            videos = [video for video in videos if video["id"] != int(request.params["selectedvideoid"])]

        video_list = videos
    else:
        video_list = None

    dba.close()

    html = Template.render("player/video-list.twig", {"videos": video_list})
    return response(html)

@middleware(MiddleWare, ["after_route_session_validation"])
@post("/api/athlete/{id}/videos/{video_id}/transcript/queue")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.Queue import Queue
    queue = Queue()

    if not queue.load("player_media_id = ? ", [request.params["video_id"]]):
        queue.action = 'transcribe'
        queue.player_id = request.params["id"]
        queue.data = {"player_media_id": request.params["video_id"]}
        queue.save()

    dba.close()

    return response("Queued!")

@middleware(MiddleWare, ["after_route_session_validation"])
@post("/api/athlete/{id}/videos/{video_id}/remove")
async def post_athlete_transcripts_queue(request, response):
    from ..orm.PlayerMedia import PlayerMedia

    player_media = PlayerMedia({"id": request.params["video_id"]})
    if player_media.load():
        player_media.is_deleted = 1
        player_media.save()

    dba.close()

    return response("Removed!")

@middleware(MiddleWare, ["after_route_session_validation"])
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

    dba.close()

    return response("Done!")

@middleware(MiddleWare, ["after_route_session_validation"])
@get("/api/athlete/{id}/transcripts/{media_id}/classification")
async def get_test_classification(request, response):
    from ..app.Player import decode_transcript
    from ..app.Scraper import aatos, classification_text
    from ..orm.PlayerTranscripts import PlayerTranscripts
    from ..orm.PlayerMedia import PlayerMedia
    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and player_media_id = ?',
                                                    params=[request.params["id"], request.params["media_id"]])
    transcript = player_transcripts.to_list(decode_transcript)[0]

    if "data" not in transcript and "transcription" not in transcript["data"] and len(
            transcript["data"]["transcription"]) == 0:
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
            text += str(counter) + "." + speaker_text + "\n\n"
            counter += 1

    player_media = PlayerMedia({"id": request.params["media_id"]})
    classification = ""
    if player_media.load():
        if str(player_media.classification) == "" or ("refresh" in request.params and request.params["refresh"] == "1"):

            chunks = chunk_text(text, 5000)
            for chunk in chunks:
                try:
                    result = aatos.generate(
                        "Classify each line of numbered text using the CLASSIFICATION RULES:\nText:" + chunk + "\nUse ONLY the following output format for each classification in the text:\nText:[Text being classified]\nClassification:[One or more classification categories comma separated]\nComment:[Short motivation for the classification of the text][LINE_FEED]\n",
                        "Human", "AI",
                        "You are an AI assistant sports psychologist evaluating a list of phrases someone has said, use the CLASSIFICATION RULES to answer the question.",
                        _context="CLASSIFICATION RULES:\n" + classification_text,
                        _stop_tokens=["Human:", "[LINEFEED]", "[LINE.Feed]"])

                    classification += result["output"]
                except Exception as e:
                    print("Error in classification:", e)
                    return response("Could not classify text.")

            dba.execute("update player_transcripts set selected_speaker = ? where id = ?",
                        [selected_speaker, transcript["id"]])
            dba.commit()

            player_media.classification = classification
            player_media.save()
        else:
            classification = str(player_media.classification.value)

        classification = "<div>" + classification.replace("\n", "</div><div>") + "</div>"
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
        \n""" + classification + "</div>"

    dba.close()

    return response(classification)

@middleware(MiddleWare, ["after_route_session_validation"])
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

    dba.close()

    return response("Done!")
