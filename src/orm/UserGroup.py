from tina4_python.ORM import *
from datetime import datetime

class UserGroup(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    name = TextField(field_size=100)
    date_created = DateTimeField(default_value=datetime.now())
    permissions = BlobField()
    is_active= IntegerField(default_value=1)

