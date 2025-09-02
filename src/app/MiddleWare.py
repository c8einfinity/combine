# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>
# Author: Jacques van Zuydam <jacques@codeinfinity.co.za>

from tina4_python.Response import Response

class MiddleWare:
    @staticmethod
    def before_route_session_validation(request, response):
        """
        Middleware function to verify the user session and redirect to the login page with a message indication that
        the session has ended.
        :param request:
        :param response:
        :return:
        """

        if (not request.session.get('logged_in')
                or request.session.get('logged_in') == False
                or (request.session.get("user_permissions") and "permissions" not in request.session.get("user_permissions"))
        ):
            print("Session invalid - redirecting to login")
            Response.redirect("/login?s_e=1")

        return request, response
