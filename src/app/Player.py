import base64
import requests
import os
import json

def get_player_results(candidate_id):
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