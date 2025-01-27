import os
import json
from importlib.metadata import metadata

import requests
from bs4 import BeautifulSoup
import re

YOUTUBE_SEARCH_URL = 'https://www.youtube.com/results?search_query='
VIDEO_REGEX = r"\{\"videoRenderer\":(.*?)\"thumbnail\":"

VIDEO_INFO_URL =  "https://www.googleapis.com/youtube/v3/videos?part=id%2C+snippet&id={{VIDEO_ID}}&key="+os.getenv("GOOGLE_API_KEY", "AIzaSyC6pg48SaZk1-t7o9lVuYf59EjkzV7Lamk")


def get_youtube_info(video_id):
    url = VIDEO_INFO_URL
    url = url.replace("{{VIDEO_ID}}", video_id)
    html = requests.get(url)
    return json.loads(html.text)


def get_video_ids(html):
    soup = BeautifulSoup(html, 'html.parser')

    html_data = []
    for tag in soup.select('script'):
        if "videoId" in tag.text:
            html_data.append(tag.text)

    matches = re.finditer(VIDEO_REGEX, "\n".join(html_data), re.MULTILINE)
    video_ids = []
    for matchNum, match in enumerate(matches, start=1):
        video_id = match.group().replace('{"videoRenderer":{"videoId":"', '').replace('","thumbnail":', '')
        meta_data = get_youtube_info(video_id)
        video_ids.append({"url": "https://www.youtube.com/watch?v="+video_id, "video_id": video_id, "metadata": meta_data })

    return video_ids


def get_youtube_videos(name="",sport="NFL Football"):
    url = YOUTUBE_SEARCH_URL+name+" "+sport+" interviews only"
    html = requests.get(url)
    return get_video_ids(html.text)
