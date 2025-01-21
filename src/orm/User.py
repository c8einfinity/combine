from tina4_python.ORM import *
from datetime import datetime
from src.orm.UserGroup import UserGroup

class User(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    first_name = TextField(field_size=100)
    last_name = TextField(field_size=100)
    email = TextField(field_size=255)
    password = TextField(field_size=255)
    date_created = DateTimeField(default_value=datetime.now())
    is_active= IntegerField(default_value=1)
    user_group_id = ForeignKeyField(IntegerField("id"), UserGroup, default_value=1)

