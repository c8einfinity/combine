# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

class SessionHandler:
    @staticmethod
    def set_user_session(request, user, user_permissions):
        """
        Function to set the user session after authentication.
        :param user_permissions:
        :param request:
        :param user:
        :return:
        """
        print("Setting user session")
        print(request.session)
        print(user)
        print(user_permissions)
        request.session.set("user", user)
        request.session.set("logged_in", True)
        request.session.set("user_permissions", user_permissions)

        request.session.save()

    @staticmethod
    def unset_user_session(request):
        """
        Function to unset a user session.
        :param request:
        :return:
        """
        print("Unsetting user session")
        print(request.session)

        request.session.set("logged_in", False)
        request.session.set("user", None)
        request.session.set("user_permissions", None)

        request.session.save()
