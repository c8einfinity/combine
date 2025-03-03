from tina4_python.ORM import *
from datetime import datetime
from .Player import Player

class Queue(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    action = StringField(default_value="transcribe")
    date_created = DateTimeField(default_value=datetime.now(), protected_field=True)
    data = BlobField(default_value="{}")
    processed= IntegerField(default_value=0)
    player_id = ForeignKeyField(IntegerField("id"), Player, default_value=1)
    priority = IntegerField(default_value=0)
