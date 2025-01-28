import base64
import json
import sys
import os.path
import yt_dlp
import torch, torchaudio
from pika import data
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment
from transformers import pipeline
import time
import Aatos
from tina4_python.Database import Database

database_path = os.getenv("DATABASE_PATH", "db-mysql-nyc3-mentalmetrix-do-user-4490318-0.c.db.ondigitalocean.com/25060:qfinder")





aatos = Aatos
aatos.LLM_URLS = [os.getenv("AATOS_URL", "http://192.168.88.99:8001")]

audio_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.getenv("HUGGING_FACE_TOKEN"),
)

audio_pipeline.to(torch.device("cuda"))

asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base",
    device="cuda"
)

def download_youtube_video(url, filename):
    error_code = None
    if not os.path.exists(filename+".wav"):
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
    else:
        print("File exists already")
    return error_code

def transcribe_audio(audio_file):
    waveform, sample_rate = torchaudio.load(audio_filename)

    with ProgressHook() as hook:
        segments = audio_pipeline({"waveform": waveform, "sample_rate": sample_rate}, min_speakers=2, max_speakers=10, hook=hook)

    audio_segment = AudioSegment.from_file(audio_filename, format="wav")

    audio_segments = []
    speakers = []
    for turn, _, speaker in segments.itertracks(yield_label=True):
        audio_segments.append(audio_segment[turn.start*1000:turn.end*1000])
        # print(speaker, turn.start, turn.end)
        speakers.append(speaker)

    processed_data = []
    counter = 0
    for audio in audio_segments:
        sample_filename = "audio/sample"+str(counter)+".wav"
        audio.export(sample_filename, format="wav")
        transcript = asr_pipeline(sample_filename, return_timestamps=True)
        processed_data.append({"speaker": speakers[counter], "transcript": transcript})
        os.remove(sample_filename)
        counter += 1

    speaker_output = []
    transcript = ""
    for data in processed_data:
        speaker_output.append({"speaker": data["speaker"].replace("_", ""), "text": data["transcript"]["text"].strip()})
        transcript += data["speaker"].replace("_", "")+": "+data["transcript"]["text"]+"\n"

    return speaker_output, transcript

def decode_data(record):
    record["data"] = json.loads(base64.b64decode(record["data"]))

    return record

# run an endless process
while True:
    try:
        dba = Database(f"mysql.connector:{database_path}",
                       os.getenv("DATABASE_USERNAME", "doadmin"),
                       os.getenv("DATABASE_PASSWORD", "doadmin"))

        queue = dba.fetch("select * from queue where processed = 0 and action = 'transcribe'").to_list(decode_data)

        if len(queue) == 1:
            print("FOUND", queue[0])

            try:
                media_file = dba.fetch("select * from player_media where id = "+str(queue[0]["data"]["player_media_id"])).to_list()

                video_url = media_file[0]["url"]
                audio_filename = "audio/"+media_file[0]["url"].replace("https://www.youtube.com/watch?v=", "").strip()+".wav"

                print("PROCESSING", video_url, audio_filename)

                error = download_youtube_video(video_url, audio_filename.replace('.wav', ''))

                transcription = transcribe_audio(audio_filename)

                data = {"transcription": transcription, "metadata": media_file[0]["metadata"], "player_media_id": media_file[0]["id"]}

                next_id = dba.get_next_id("player_transcripts")
                dba.insert("player_transcripts", {"data": data, "id": next_id, "player_id": media_file[0]["player_id"], "player_media_id": media_file[0]["id"]})


                dba.update("queue", {"id": queue[0]["id"], "processed": 1, "data": data})
                dba.commit()

                dba.close()

                os.remove(audio_filename)
            except Exception as e:
                print("ERROR", str(e))
                dba.update("queue", {"id": queue[0]["id"], "processed": 1, "data": {"error": str(e)}})

            time.sleep(1)
        else:
            print("LOOKING...")
            time.sleep(1)

        dba.commit()
        dba.close()
    except KeyboardInterrupt:
        print("Application Terminated")
