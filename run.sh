poetry env use 3.12
poetry update --no-cache
poetry export -f requirements.txt --output requirements.txt
poetry run jurigged app.py stop
