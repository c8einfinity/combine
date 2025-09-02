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
        response.headers["Access-Control-Allow-Methods"] = "*"

        if (not request.session.get('logged_in')
            and request.session.get('logged_in') != False
            and request.session.get("user_permissions")
            and "permissions" in request.session.get("user_permissions")
        ):
            Response.redirect("/login?s_e=1")

        return request, response
