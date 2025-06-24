from tina4_python.ORM import *

class AdminSetting(ORM):
    id = IntegerField(auto_increment=True, primary_key=True, default_value=0)
    setting_key = StringField(default_value="")
    setting_value = StringField(default_value="")
    created_at = DateTimeField(default_value=datetime.now(), protected_field=True)
    updated_at = DateTimeField(default_value=datetime.now(), protected_field=True)