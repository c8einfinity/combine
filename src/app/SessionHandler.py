# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from ..app.UserGroups import UserGroups

class SessionHandler:
    @staticmethod
    def set_user_session(request, user):
        """
        Function to set the user session after authentication.
        :param request:
        :param user:
        :return:
        """
        request.session.set("user", user)
        request.session.set("logged_in", True)

        user_group = UserGroups.get_user_group_data_by_id(user["user_group_id"])

        request.session.set("user_permissions", UserGroups.get_condensed_user_group_permission_list(user_group))

        request.session.save()

    @staticmethod
    def unset_user_session(request):
        """
        Function to unset a user session.
        :param request:
        :return:
        """
        request.session.set("logged_in", False)
        request.session.set("user", None)
        request.session.set("permissions", None)

        request.session.save()
