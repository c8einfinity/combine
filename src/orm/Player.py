from tina4_python.ORM import *
from datetime import datetime

class Player(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    username = TextField(field_size=200, primary_key=True)
    first_name = TextField(field_size=200)
    last_name = TextField(field_size=200)
    email = TextField(field_size=255)
    image = BlobField()
    height = TextField(field_size=20)
    team = TextField(field_size=200)
    mobile = TextField(field_size=30)
    sport = TextField(field_size=200)
    position = TextField(field_size=200)
    home_town = TextField(field_size=200)
    major = TextField(field_size=200)
    date_of_birth = DateTimeField(protected_field=True)
    date_created = DateTimeField(default_value=datetime.now(), protected_field=True)
