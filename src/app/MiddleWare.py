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
        if request.session.get("logged_in") is not None and request.session.get("logged_in") == True:
            if request.session.get("user_permissions") is None and request.session.get("user") is not None:
                # get the user permissions
                from ..app.UserGroups import UserGroups
                user = request.session.get("user")
                if "user_group_id" not in user:
                    Response.redirect("/login?s_e=1")

                user_group = UserGroups.get_user_group_data_by_id(user["user_group_id"])
                user_permissions = UserGroups.get_holistic_user_group_permission_list(user_group)
                request.session.set("user_permissions", user_permissions)

        if (not request.session.get('logged_in')
                or request.session.get('logged_in') == False
                or (request.session.get("user_permissions") and "permissions" not in request.session.get("user_permissions"))
        ):
            print("Session invalid - redirecting to login")
            Response.redirect("/login?s_e=1")

        return request, response
