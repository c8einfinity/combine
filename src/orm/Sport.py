from tina4_python.ORM import *

class Sport(ORM):
    id = IntegerField(auto_increment=False, primary_key=True, default_value=0)
    name = TextField(field_size=200, primary_key=False)
    date_created = DateTimeField(default_value=datetime.now(), protected_field=True)
    date_updated = DateTimeField(default_value=datetime.now(), protected_field=True)