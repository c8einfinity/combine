# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from tina4_python.Constant import HTTP_OK, TEXT_HTML

class MiddleWare:
    @staticmethod
    def after_route_session_validation(request, response):
        """
        Middleware function to verify the user session and redirect to the login page with a message indication that
        the session has ended.
        :param request:
        :param response:
        :return:
        """
        response.headers["Access-Control-Allow-Methods"] = "*"

        if not request.session.get('logged_in'):
            response.content = "<script>window.location.href='/login?s_e=1';</script>"
            response.content_type = TEXT_HTML
            response.http_code = HTTP_OK

        return request, response
