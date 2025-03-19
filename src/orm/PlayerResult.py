from tina4_python.ORM import *
from datetime import datetime

class PlayerResult(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    data = BlobField()
    player_id = IntegerField(default_value=0)
    latest = IntegerField(default_value=0)
    date_created = DateTimeField(default_value=datetime.now(), protected_field=True)
    transcription = BlobField()
    transcript_hash = TextField(field_size=255)