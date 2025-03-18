# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

class UserGroup:
    @staticmethod
    def get_user_group_data():
        """
        Function to get all user group data.
        :return:
        """
        from ..orm.UserGroup import UserGroup

        user_group = UserGroup().select(["id", "name", "permissions"], "id <> ?", [0])

        return user_group.to_array()
