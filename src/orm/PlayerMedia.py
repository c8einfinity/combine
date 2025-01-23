from tina4_python.ORM import *
from datetime import datetime
from .Player import Player

class PlayerMedia(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    url = TextField(field_size=200)
    media_type = DateTimeField(protected_field=True)
    date_created = DateTimeField(default_value=datetime.now(), protected_field=True)
    is_valid= IntegerField(default_value=0)
    player_id = ForeignKeyField(IntegerField("id"), Player, default_value=1)