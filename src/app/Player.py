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

def submit_player_results(first_name, last_name, text="", candidate_id=""):

    data = {"first_name": first_name, "last_name": last_name,
            "candidate_id": candidate_id, "text": text}

    results = requests.post(os.getenv("TEAMQ_RESULTS_ENDPOINT"),
                            json=data,
                            headers={"Content-Type": "application/json",
                                     "Authorization": "Bearer " + os.getenv("TEAMQ_API_KEY")} )
    return results.json()


