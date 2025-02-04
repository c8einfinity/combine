import re
import requests
import os.path
from .. import Aatos
import json
from bs4 import BeautifulSoup, Comment, NavigableString
from semantic_text_splitter import TextSplitter

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


def get_classification_text(text, classification):

    pass


def get_speaker_from_transcript(transcript, player_name):

    pass


aatos = Aatos
aatos.LLM_URLS = [os.getenv("AATOS_URL", "http://192.168.88.99:8001")]


prompt = ("Output the player information in the following JSON format ONLY if you can determine the data:\n" +
          json.dumps({"name": "[Player Name]", "height": "[Player Height]", "weight": "[Player Weight]",
                      "sport": "[Player Sport]", "year": "[Player Year]", "homeTown": "[Player Hometown]",
                      "school": "[Player School]", "position": "[Player Position]", "major": "[Player Major]"}))

system_prompt = "You are AI assistant parsing scraped data from the BIO of an athlete from a website. Extract the player's information as required. Determine the sport by the Position played. Only answer with the requested JSON format."

replace_text = ["html", "Skip to main content: #main-content", "Close Ad"]


def chunk_text(text, max_characters=24000):
    # Optionally can also have the splitter not trim whitespace for you
    splitter = TextSplitter(max_characters)
    return splitter.chunks(text)


def clean_me(html):
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup.select('head'):
        tag.extract()
    for tag in soup.select('footer'):
        tag.extract()
    for tag in soup.select('style'):
        tag.extract()
    for tag in soup.select('script'):
        tag.extract()

    data = soup.get_text(separator='\n').strip().replace('\n\n', ' ')

    if data.strip() == "":
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.select('script'):
            data += tag.get_text(separator='\n').strip().replace('\n\n', ' ')

    return data


def html2text(html: str) -> str:
    soup = BeautifulSoup(html, features="html.parser")
    for tag in soup.select('head'):
        tag.extract()
    for tag in soup.select('footer'):
        tag.extract()
    for tag in soup.select('style'):
        tag.extract()
    for tag in soup.select('script'):
        tag.extract()
    texts = []
    for element in soup.descendants:
        if isinstance(element, NavigableString) and not isinstance(element, Comment):
            if element.parent and element.parent.name == "code":
                texts.append("--")
                continue
            s = element.strip()
            if s:
                texts.append(
                    f"{s}: {element.parent["href"]}"
                    if element.parent and element.parent.name == "a" else
                    s
                )
    data = "\n".join(text for text in texts)

    if data.strip() == "html":
        print("See data in scripts")
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.select('script'):
            data += tag.get_text(separator='\n').strip().replace('\n\n', ' ')

    for text in replace_text:
        data = data.replace(text, "")
    data = data.encode("ascii", "ignore")
    return data.decode()


def get_html_content(url):
    html = requests.get(url)
    return clean_me(html.text)




def get_player_profile(url):
    scraped_data = get_html_content(url)
    data_chunks = chunk_text(scraped_data)

    collected_data = {}
    for data_chunk in data_chunks:
        # print("CHUNK", data_chunk, len(data_chunk))
        result = aatos.generate(prompt,
                                "Human", "AI",
                                system_prompt,
                                _context="COLLECTED DATA:\n" + json.dumps(
                                    collected_data) + "\nSCRAPED DATA:\n" + data_chunk)
        try:
            print(result["output"])
            if "```json" in result["output"]:
                result["output"] = result["output"].split("```")[1].replace("json\n{", "{")


            profile_data = json.loads(result["output"])
            print(profile_data, len(data_chunk))
            for key, value in profile_data.items():
                if value is not None:
                    collected_data[key] = value
        except Exception as e:
            print(e)

    return collected_data

