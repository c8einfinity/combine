import base64
import io

import requests
import os
import json

from PIL import Image
from PIL.Image import Resampling


def get_player_results(candidate_id):
    """
    Fetch results from the API
    :param candidate_id:
    :return:
    """
    results = requests.post(os.getenv("TEAMQ_RESULTS_ENDPOINT"),
                            json={"candidate_id": candidate_id},
                            headers={"Content-Type": "application/json",
                                     "Authorization": "Bearer " + os.getenv("TEAMQ_API_KEY")} )
    return results.json()

def submit_player_results(first_name, last_name, image="", text="", candidate_id=""):

    data = {"first_name": first_name, "last_name": last_name, "image": image,
            "candidate_id": candidate_id, "text": text}

    results = requests.post(os.getenv("TEAMQ_RESULTS_ENDPOINT"),
                            json=data,
                            headers={"Content-Type": "application/json",
                                     "Authorization": "Bearer " + os.getenv("TEAMQ_API_KEY")} )
    return results.json()

def player_bio_complete(player_id):
    """
    Check if the player has all the required records
    :param player_id:
    :return:
    """
    from ..orm.Player import Player

    player = Player({"id": player_id})
    if player.load():
        player = player.to_dict()
        completed_fields = 0
        if player["username"]:
            completed_fields += 1
        if player["first_name"]:
            completed_fields += 1
        if player["last_name"]:
            completed_fields += 1
        if player["image"]:
            completed_fields += 1
        if player["sport"]:
            completed_fields += 1
        if player["position"]:
            completed_fields += 1
        if player["date_of_birth"]:
            completed_fields += 1
        if player["home_town"]:
            completed_fields += 1
        if player["team"]:
            completed_fields += 1
        return completed_fields == 9

    return None

def get_player_stats():
    """
    Runs a query to return the total number of athletes in the database, and the status of their bio and linked videos
    :return:
    """
    from ..orm.Player import Player

    players = Player.__dba__.fetch_one("select count(*) as total_players from player")

    player_bio_linked = Player.__dba__.fetch_one("select count(*) as total_bio_links from player where is_bio_links_created = 1")

    player_videos_linked = Player.__dba__.fetch_one("select count(*) as total_videos from player where is_video_links_created = 1")

    return {
        "total_players": players['total_players'],
        "total_bio_links": player_bio_linked['total_bio_links'],
        "total_videos": player_videos_linked['total_videos']
    }

def resize_profile_image(image_data):
    """
    Resize the profile image to under 64kb
    :param image_data:
    :return:
    """
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    # Convert to RGB if necessary
    if image.format in ["PNG", "WEBP"]:
        image = image.convert("RGB")

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