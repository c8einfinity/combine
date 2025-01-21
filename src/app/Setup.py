from tina4_python import tina4_auth
from tina4_python import Debug

def check_setup(dba):
    from ..orm.User import User
    # check for an admin user
    user = User()

    if not user.load("is_active = ? and user_group_id = ?", [1, 1]):
        Debug.error("Admin user already exists")
        user.first_name = "Admin"
        user.last_name = "Admin"
        user.email = "admin@qfinder.io"
        user.password = tina4_auth.hash_password("QFinder1234!")
        user.is_active = 1
        user.user_group_id = 1
        user.save()
    else:
        Debug.info("Admin user already exists")


