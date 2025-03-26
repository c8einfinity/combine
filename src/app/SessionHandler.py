# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

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

        request.session.save()

    @staticmethod
    def unset_user_session(request):
        """
        Function to unset a user session.
        :param request:
        :return:
        """
        request.session.set("user", None)
        request.session.set("logged_in", False)

        request.session.save()
