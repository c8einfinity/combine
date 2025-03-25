# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

import json
from ..app.Roles import Roles
from ..app.Utility import get_data_tables_filter
from tina4_python import Debug
from tina4_python.Constant import HTTP_OK, HTTP_SERVER_ERROR, TEXT_PLAIN, APPLICATION_JSON
from tina4_python.Template import Template

class UserGroup:
    @staticmethod
    def get_user_group_data():
        """
        Function to get all user group data.
        :return:
        """
        from ..orm.UserGroup import UserGroup

        user_group = UserGroup().select(["id", "name", "permissions"], "id <> ?")

        return user_group.to_array()

    @staticmethod
    def get_user_group_data_by_id(user_group_id):
        """
        Function to get all user group data.
        :return:
        """
        from ..orm.UserGroup import UserGroup

        Debug.error("Hellooo", user_group_id)

        user_group = UserGroup().select(
            ["id", "name", "permissions"],
            "id = ?",
            [str(user_group_id)]
        )

        return user_group.to_array()

    @staticmethod
    def get_user_group_landing(response):
        """
        Function to get the user group landing page
        :param response:
        :return:
        """
        data = {
            "roles": Roles.get_initial_roles_permission_list()
        }

        return response(Template.render_twig_template("dashboard/user_groups.twig", data))

    @staticmethod
    def get_user_groups(request, response):
        """
        Function to get all the user groups
        :param request:
        :param response:
        :return:
        """
        if "draw" not in request.params:
            return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

        from ..orm.UserGroup import UserGroup

        data_tables_filter = get_data_tables_filter(request)

        where = "id <> ?"

        if data_tables_filter["where"] != "":
            where += " and " + data_tables_filter["where"]

        user_groups = UserGroup().select(["id", "name", "date_created", "permissions", "is_active"],
                                         where,
                                         [0],
                                         order_by=data_tables_filter["order_by"],
                                         limit=data_tables_filter["length"],
                                         skip=data_tables_filter["start"])

        data = user_groups.to_paginate()
        data["draw"] = request.params["draw"]

        for user_group in data["data"]:
            permission_string = ""

            if "permissions" in user_group and user_group["permissions"] and user_group["permissions"] != "None":
                permissions = json.loads(user_group["permissions"])
            else:
                permissions = Roles.get_initial_roles_permission_list()["access_list"]

            for permission in permissions:
                access_point = permission["access_point"]
                permission_entry = ", ".join("{}={}".format(*i) for i in permission["permissions"].items())

                permission_string += f"&bull; <b>{access_point}:</b> {permission_entry}</br>"

            user_group["permissions"] = permission_string

        return response(data)

    @staticmethod
    def post_user_group(request, response):
        """
        Function to add a user group
        :param request:
        :param response:
        :return:
        """
        from ..orm.UserGroup import UserGroup

        user_group = UserGroup(request.body)

        success = False
        output_message = "Failed to save user group!"

        if user_group.save():
            success = True
            output_message = "User group saved"

        result = {
            "success": success,
            "message": output_message
        }

        return response(result , HTTP_OK, APPLICATION_JSON)

    @staticmethod
    def delete_user_group(request, response):
        """
        Function to delete a user group
        :param request:
        :param response:
        :return:
        """
        from ..orm.UserGroup import UserGroup

        user_group = UserGroup({"id": request.params["id"]})

        if user_group.delete():
            return response("User group deleted")
        else:
            return response("Failed to delete user group!")
