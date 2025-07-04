import ast
import base64
import io
import json
import re
from json import JSONDecodeError

import requests
import os
import csv

from PIL import Image
from PIL.Image import Resampling

from src.app.QueueUtility import QueueUtility


def get_player_results(candidate_id):
    """
    Fetch results from the API
    :param candidate_id:
    :return:
    """
    try:
        results = requests.post(f"{os.getenv("TEAMQ_ENDPOINT")}/recruit/assessment",
                                json={"candidate_id": candidate_id},
                                headers={"Content-Type": "application/json",
                                         "Authorization": "Bearer " + os.getenv("TEAMQ_API_KEY")} )
    except Exception as e:
        print(f"Error fetching results: {e}")
        return {"error": str(e), "player": {"html": ""}, "coach": {"html": ""}, "scout": {"html": ""}}

    try:
        report = results.json()

        if "player" in report:
            return report
    except JSONDecodeError:
        print("JSON Error from TEAMQ result:", results)

    print("No result:", results)
    return {"error": "No results found", "player": {"html": ""}, "coach": {"html": ""}, "scout": {"html": ""}}

def split_trim_minify(text):
    """
    For the HTML results coming in from the API.
    :param text:
    :return:
    """
    # Split the text by new lines
    lines = text.split('\n')
    # Trim each line and join them into one line
    minified_text = ' '.join(line.strip() for line in lines)
    return minified_text

def get_sport_position_ids(sport_name, position_name):
    """
    Get the sport and position ids from the database
    :param sport_name:
    :param position_name:
    :return:
    """
    from tina4_python import Debug
    from ..orm.Sport import Sport
    from ..orm.SportPosition import SportPosition

    # get the sport and position ids from the database
    sport = Sport().select("id, name", limit=1, filter="name = ?", params=[str(sport_name)])
    sport = sport.to_list()

    if len(sport) == 0:
        Debug.error(f"Sport {sport_name} not found in the database")
        return {"error": "Sport not found"}

    position = SportPosition().select("id, name", limit=1, filter="name = ?", params=[str(position_name)])
    position = position.to_list()

    if len(position) == 0:
        Debug.error(f"Position {position_name} not found in the database")
        return {"error": "Position not found"}

    return {"sport_id": sport[0]["id"], "position_id": position[0]["id"]}

def submit_player_results(first_name, last_name, image="", text="", candidate_id="", sport="", position="", date_of_birth="", home_town="", team=""):
    """
    Submit the player results to the API to get the Receptiviti results
    :param team:
    :param home_town:
    :param date_of_birth:
    :param position:
    :param sport:
    :param first_name:
    :param last_name:
    :param image:
    :param text:
    :param candidate_id:
    :return:
    """
    from tina4_python import Debug

    # get the sport and position ids from the database
    sport_position = get_sport_position_ids(sport, position)

    data = {"first_name": first_name, "last_name": last_name, "image": image,
            "candidate_id": candidate_id, "text": text, "sport_id": sport_position["sport_id"],
            "position_id": sport_position["position_id"], "dob": date_of_birth, "home_town": home_town, "team": team}

    Debug.info(f"submit_player_results: {data}")

    try:
        results = requests.post(f"{os.getenv("TEAMQ_ENDPOINT")}/recruit/assessment",
                            json=data,
                            headers={"Content-Type": "application/json",
                                     "Authorization": "Bearer " + os.getenv("TEAMQ_API_KEY")} )
        return results.json()
    except Exception as e:
        Debug.error(f"submit_player_results: {e}")
        return {"error": str(e)}

def submit_player_teamq_details(player):
    """
    Submit the player details to the TEAMQ API
    :param player:
    :return:
    """
    from tina4_python import Debug

    if type(player) is not dict:
        player = player.to_dict()

    if "candidate_id" not in player or player["candidate_id"] is None or player["candidate_id"] == "":
        Debug.error("submit_player_teamq_details: player does not have a candidate_id")
        return {"error": "Error updating TeamQ, athlete does not have a TeamQ id, submit the player results first"}

    sport_position = get_sport_position_ids(player["sport"], player["position"])

    data = {
        "first_name": player["first_name"],
        "last_name": player["last_name"],
        "image": player["image"],
        "sport_id": sport_position["sport_id"],
        "position_id": sport_position["position_id"],
        "date_of_birth": player["date_of_birth"],
        "home_town": player["home_town"],
        "team": player["team"]
    }

    Debug.info(f"submit_player_teamq_details: {data}")

    try:
        response = requests.put(f"{os.getenv('TEAMQ_ENDPOINT')}/player/{player["candidate_id"]}/update-candidate",
                                 json=data,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.getenv("TEAMQ_API_KEY")})
        return response.json()
    except Exception as e:
        Debug.error(f"submit_player_teamq_details: {e}")
        return {"error": str(e)}

def player_bio_complete(player_id):
    """
    Check if the player has all the required records
    :param player_id:
    :return:
    """
    from ..orm.Player import Player

    player = Player().select("*", filter="id = ?", params=[player_id], limit=1)
    if player.count == 1:
        player = player[0]
        required_fields = ["first_name", "last_name", "image", "sport", "position", "date_of_birth", "home_town", "team"]
        return all(player[field] for field in required_fields)

    return None

def player_report_sent(player_id):
    """
    Check if the player results have been sent and created
    :param player_id:
    :return:
    """
    from ..orm.PlayerResult import PlayerResult

    player_result = PlayerResult().select("id", filter="player_id = ? and data is not NULL", params=[player_id], limit=1, order_by="date_created desc")
    if len(player_result.to_list()) > 0:
        return True

    return False

def remove_repeated_text(input_string):
    words = input_string.split()
    seen = set()
    result = []

    for word in words:
        if word not in seen:
            seen.add(word)
            result.append(word)

    return ' '.join(result)

def replace_repeats(text):
    # Use regex to find repeated characters outside of words
    pattern = re.compile(r'\b(\w*?)([^\W\d_])\2{2,}(\w*?)\b')

    # Replace the repeated characters with a single instance
    result = pattern.sub(lambda m: m.group(1) + m.group(2) + m.group(3), text)

    return result

def decode_transcript(record):
    try:
        record["data"] = ast.literal_eval(base64.b64decode(record["data"]).decode("utf-8"))

        # clean up of funny chars & duplicated text
        transcription = []
        for speaker in record["data"]["transcription"]:
            text = ''.join([i if ord(i) < 128 else '' for i in speaker["text"]])
            text = text.replace("-", "").strip()

            if text != "" and len(text) > 1:
                speaker["text"] = remove_repeated_text(replace_repeats(text))+" "
                transcription.append(speaker)

        record["data"]["transcription"] = transcription

    except Exception as e:
        record["data"] = str(e)
    return record

def get_player_transcript(player_id: int) -> str:
    """
    Get the player transcript from the approved videos
    :param player_id:
    :return:
    """
    from ..orm.PlayerTranscripts import PlayerTranscripts
    from ..orm.PlayerResult import PlayerResult
    from ..orm.Player import Player

    player = Player({"id": player_id})
    player.load()

    player_transcripts = PlayerTranscripts().select("*", 'player_id = ? and verified_user_id > 0 and exists (select id from player_media where id = t.player_media_id and is_valid = 1) ',
                                                    params=[player_id])
    text = ""

    transcripts = player_transcripts.to_list(decode_transcript)
    for transcript in transcripts:
        for speaker in transcript["data"]["transcription"]:
            if speaker and "speaker" in speaker:
                if speaker["speaker"] == transcript["selected_speaker"]:
                    text += speaker["text"]

    # remove any none latin characters from text
    text = ''.join([i if ord(i) < 128 else '' for i in text])

    return str(text)

def get_player_stats():
    """
    Runs a query to return the total number of athletes in the database, and the status of their bio and linked videos
    :return:
    """
    from ..orm.Player import Player

    players = Player.__dba__.fetch_one("select count(*) as total_players from player")

    player_bio_linked = Player.__dba__.fetch_one("select count(*) as total_bio_links from player where "
                                                 "is_bio_links_created = 1")

    player_videos_linked = Player.__dba__.fetch_one("select count(*) as total_videos from player where "
                                                    "is_video_links_created = 1")

    confirmed_players = Player.__dba__.fetch_one("select count(distinct player.id) as total_confirmed_players from player "
                                                 "join player_media on player.id = player_media.player_id "
                                                 "join player_transcripts on player.id = player_transcripts.player_id "
                                                 "and player_media.id = player_transcripts.player_media_id "
                                                 "and player_media.is_sorted = 1 "
                                                 "and player_media.is_deleted = 0 "
                                                 "and player_media.is_valid = 1 "
                                                 "and player_transcripts.verified_user_id > 0")

    return {
        "total_players": players['total_players'] if players else 0,
        "total_bio_links": player_bio_linked['total_bio_links'] if player_bio_linked else 0,
        "total_videos": player_videos_linked['total_videos'] if player_videos_linked else 0,
        "total_confirmed_players": confirmed_players['total_confirmed_players'] if confirmed_players else 0
    }

def resize_profile_image(image_data):
    """
    Resize the profile image to under 64kb
    :param image_data:
    :return:
    """
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    # Convert to RGB if necessary
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        # Create a white background image
        background = Image.new("RGB", image.size, (255, 255, 255))
        # Paste the image on the background, using the alpha channel as mask
        background.paste(image, mask=image.split()[3] if image.mode == "RGBA" else image)
        image = background

    # resize the image to max width or height of 420px
    image.thumbnail((420, 420), Resampling.BICUBIC)

    # Compress the image until it's under 64KB
    quality = 95
    while True:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        if buffer.tell() <= 48 * 1024:  # 64KB
            break
        quality -= 5
        if quality < 10:
            raise Exception("Cannot resize image to be under 64KB")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def import_csv_player_data(file_data):
    """
    Import player data from a CSV file
    :param file_data:
    :return:
    """
    from ..orm.Player import Player
    from src.app.QueueUtility import QueueUtility
    import csv
    import io

    try:
        # Validate file_data
        if not file_data or not isinstance(file_data, str):
            raise ValueError("Invalid file data provided")

        read_data = csv.DictReader(io.StringIO(file_data), delimiter=",")
        count = 0
        queue = QueueUtility()

        for row in read_data:
            # Validate required fields
            if not all(key in row for key in ["first_name", "last_name", "sport", "position", "team"]):
                raise ValueError(f"Missing required fields in row: {row}")

            # Check if the player already exists
            player = Player().select("*", filter="first_name = ? and last_name = ?", params=[row['first_name'], row['last_name']], limit=1)
            if player.count == 0:
                # Create a new player
                player = Player({
                    "first_name": row['first_name'],
                    "last_name": row['last_name'],
                    "sport": row['sport'],
                    "position": row['position'],
                    "team": row['team'],
                    "is_bio_links_created": 0,
                    "is_video_links_created": 0
                })
                player.save()

                count += 1
                player = player.to_dict()
                queue.add_item("process_player", {"player_id": player["id"]})

        return count

    except Exception as e:
        print(f"Error importing CSV player data: {e}")
        Debug.error(f"Error importing CSV player data: {e}")
        return 0

