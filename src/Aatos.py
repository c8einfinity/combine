import json
import os
import requests
from tina4_python.Debug import Debug

LLM_URLS = [""]
BALANCER_INDEX = 0
SEED = 990011
RETRY_COUNT = 5

def generate(_prompt, _human_name, _ai_name, _system_prompt=None, _summary=None, _context="", _history=None,
                   _temperature=0.0, _top_k=5, _top_p=0.5, _max_tokens=24000, _model="phi3:mini", _seed=SEED, _stop_tokens=None, _chat_handler=None):
    global BALANCER_INDEX
    global LLM_URLS

    if _history is None:
        _history = []
    if _summary is None:
        _summary = ""

    if _history is None:
        _history = []

    split_name = _human_name.split(" ")

    stop_tokens = ["assistant"]

    if _stop_tokens is not None:
        # check if _stop_tokens is a list and make it a list
        if not isinstance(_stop_tokens, list):
            stop_tokens = [str(_stop_tokens)]
        else:
            stop_tokens = _stop_tokens

    headers = {'Authorization': f"Bearer {os.getenv('AATOS_API_KEY')}"}

    data = {
        "prompt": _prompt,
        "model_name": _model,
        "system_prompt": _system_prompt,
        "ai_name": _ai_name,
        "human_name": _human_name,
        "options": {
            "temperature": _temperature,
            "seed": _seed,
            "stop": stop_tokens
        },
        "summary": _summary,
        "context": _context,
        "history": _history
    }

    response = requests.post(url=f"{os.getenv('AATOS_URL')}/api/generate", json=data, headers=headers)

    if not response.ok:
        return {"output": None, "error": "Server Error"}

    reply = response.json()
    try:
        if "message_id" in reply and reply["message_id"] is not None:
            reply = get_valid_message(reply["message_id"])
            return {"output": reply["response"]}
    except Exception as e:
        reply = {"output": None, "error": str(e)}
        return reply

def get_valid_message(message_id, retry_count=0):
    reply = get_message(message_id)
    if "response" in reply or retry_count >= RETRY_COUNT:
        return reply
    Debug.debug(["RETRYING GET MESSAGE", retry_count, reply])
    import time
    time.sleep(1)
    return get_valid_message(message_id, retry_count + 1)

def get_message(message_id):
    try:
        headers = {'Authorization': f"Bearer {os.getenv('AATOS_API_KEY')}"}

        response = requests.get(url=os.getenv('AATOS_URL') + f"/api/generate/{message_id}", headers=headers)

        if not response.ok:
            return {"error": "Server Error"}
        return response.json()
    except Exception as error:
        return {"error": str(error)}
