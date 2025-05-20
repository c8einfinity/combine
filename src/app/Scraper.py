import re
import requests
import os.path
from .Google import Google
import tina4_python
from .. import Aatos
import json
from bs4 import BeautifulSoup, Comment, NavigableString
from semantic_text_splitter import TextSplitter

YOUTUBE_SEARCH_URL = 'https://www.youtube.com/results?search_query='
VIDEO_REGEX = r"\{\"videoRenderer\":(.*?)\"thumbnail\":"

VIDEO_INFO_URL = "https://www.googleapis.com/youtube/v3/videos?part=id%2C+snippet&id={{VIDEO_ID}}&key=" + os.getenv(
    "GOOGLE_API_KEY", "AIzaSyC6pg48SaZk1-t7o9lVuYf59EjkzV7Lamk")


def get_player_bio_urls(player_name, player_sport):
    """
    Gets a list of bio information
    :param player_name:
    :return:
    """

    search_criteria = f"{player_name} full player bio for {player_sport} latest"

    if player_sport == "American Football":
        search_criteria = f"{player_name} full player bio for NFL latest"
    if player_sport == "EU Football/ Soccer":
        search_criteria = f"{player_name} full player bio for Soccer latest"

    results = Google.search(search_criteria)

    final_results = []
    for result in results:
        if "nfl" in result or "football" in result or "soccer" in result:
            final_results.append(result)

    return final_results


def get_youtube_info(video_id):
    """
    Get YouTube information
    :param video_id:
    :return:
    """
    url = VIDEO_INFO_URL
    url = url.replace("{{VIDEO_ID}}", video_id)
    html = requests.get(url)
    return json.loads(html.text)


def get_video_ids(html):
    """
    Get Video Ids
    :param html:
    :return:
    """
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
        video_ids.append(
            {"url": "https://www.youtube.com/watch?v=" + video_id, "video_id": video_id, "metadata": meta_data})

    return video_ids


def get_youtube_videos(name="", sport="NFL, American Football"):
    """
    Get YouTube video urls
    :param name:
    :param sport:
    :return:
    """
    url = YOUTUBE_SEARCH_URL +  sport + ",interviews with "+name
    html = requests.get(url)
    return get_video_ids(html.text)


def get_classification_text(text, classification):
    pass


def get_speaker_from_transcript(transcript, player_name):
    pass


aatos = Aatos
aatos.LLM_URLS = [os.getenv("AATOS_URL", "http://73.155.227.31:40008/")]

prompt = (
            "Output the player information in the following JSON format ONLY if you can determine the data, Use ONLY the fields below:\n" +
            json.dumps({"name": "[Player Name]", "height": "[Player Height]", "weight": "[Player Weight]",
                        "sport": "[Player Sport]", "year": "[Player Year]", "homeTown": "[Player Hometown]",
                        "school": "[Player School]", "position": "[Player Position]", "major": "[Player Major]"}))

system_prompt = "You are AI assistant parsing scraped data from the BIO of an athlete from a website. Extract the player's information as required. Determine the sport by the Position played. Only answer with the requested JSON format."

replace_text = ["html", "Skip to main content: #main-content", "Close Ad"]

classification_text = open(tina4_python.root_path + "/src/app/classification_rules.txt", "r").read()


def chunk_text(text, max_characters=10000):
    """
    Chunk the text into segments
    :param text:
    :param max_characters:
    :return:
    """
    # Optionally can also have the splitter not trim whitespace for you
    splitter = TextSplitter(max_characters)
    return splitter.chunks(text)


def clean_me(html):
    """
    Clean me
    :param html:
    :return:
    """
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
    """
    HTML to TEXT
    :param html:
    :return:
    """
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


def get_player_profile(url, collected_data=None):
    """
    Get player profile
    :param url:
    :param collected_data:
    :return:
    """
    scraped_data = get_html_content(url)
    data_chunks = chunk_text(scraped_data)

    if collected_data is None:
        collected_data = {}

    for data_chunk in data_chunks:
        # print("CHUNK", data_chunk, len(data_chunk))
        result = aatos.generate(prompt,
                                "Human", "AI",
                                system_prompt,
                                _context="COLLECTED DATA:\n" + json.dumps(
                                    collected_data) + "\nSCRAPED DATA:\n" + data_chunk)
        try:
            if "```json" in result["output"]:
                result["output"] = result["output"].split("```")[1].replace("json\n{", "{")

            profile_data = json.loads(result["output"])

            for key, value in profile_data.items():
                if value is not None:
                    collected_data[key] = value

        except Exception as e:
            print(e, result["output"])

    return collected_data
