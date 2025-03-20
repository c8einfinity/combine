from tina4_python.ORM import *
from datetime import datetime
from .Player import Player
from .PlayerMedia import PlayerMedia

class PlayerTranscripts(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    date_created = DateTimeField(default_value=datetime.now(), protected_field=True)
    data = BlobField(default_value="{}")
    player_media_id = ForeignKeyField(IntegerField("id"), PlayerMedia, default_value=1)
    player_id = ForeignKeyField(IntegerField("id"), Player, default_value=1)
    classification = BlobField(default_value="{}")
    selected_speaker = StringField(default_value="SPEAKER00")
    user_verified_speaker = IntegerField(default_value=0)
