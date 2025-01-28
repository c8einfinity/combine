import sys
import os.path
import yt_dlp
import torch, torchaudio
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment
from transformers import pipeline
import lib.Aatos

aatos = Aatos
aatos.LLM_URLS = [os.getenv("AATOS_URL", "http://192.168.88.99:8001")]


def download_youtube_video(url, filename):
    print("DOWNLOADING", url)
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': filename
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.cache = None
        error_code = ydl.download([url])

url = "https://www.youtube.com/watch?v=MGZGGClEk90"
audio_filename = "audio/MGZGGClEk90.wav"


download_youtube_video(url, audio_filename.replace('.wav', ''))
