import json
import requests

LLM_URLS = [""]
BALANCER_INDEX = 0
SEED = 990011


def generate(_prompt, _human_name, _ai_name, _system_prompt=None, _summary=None, _context="", _history=None,
                   _temperature=0.0, _top_k=5, _top_p=0.5, _max_tokens=512, _model="Llama-3.2", _seed=SEED, _stop_tokens=None, _chat_handler=None):
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

    headers = {'Authorization': 'Bearer ABCDEF'}
    data = {
        "prompt": _prompt,
        "ai": {
            "modelName": _model,
            "name": _ai_name,
            "humanName": _human_name,
            "temperature": _temperature,
            "topK": _top_k,
            "topP": _top_p,
            "maxTokens": _max_tokens,
            "repeatPenalty": 1.2,
            "repeatTokens": 512,
            "seed": _seed,
            "systemPrompt": _system_prompt,
            "stop": stop_tokens
        },
        "summary": _summary,
        "context": _context,
        "history": _history
    }

    if _chat_handler is not None:
        _chat_handler.debug(["BALANCER", BALANCER_INDEX, LLM_URLS[BALANCER_INDEX]])
        _chat_handler.debug(["PAYLOAD: ", json.dumps(data) ])

    BALANCER_INDEX += 1
    if BALANCER_INDEX > len(LLM_URLS)-1:
        BALANCER_INDEX = 0

    reply = requests.post(url=LLM_URLS[BALANCER_INDEX] + "/api/generate", json=data, headers=headers)


    if not reply.ok:
        reply = {"output": None, "error": "Server Error"}

    try:
        if _chat_handler is not None:
            _chat_handler.debug("-- REPLY: "+ json.dumps(reply.json()))
        return reply.json()
    except Exception as e:
        reply = {"output": None, "error": str(e)}
        return reply
