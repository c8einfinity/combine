## Installation

Install UV and FFmpeg 

```
apt install ffmpeg -y
poetry install
poetry run pip install pika
poetry run pip install tina4_python
poetry run pip install mysql-connector-python
poetry run pip install pyannote.audio
poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
poetry run pip install transformers
```