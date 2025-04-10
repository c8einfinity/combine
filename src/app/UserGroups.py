# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

import json
from .. import dba
from ..app.Utility import get_data_tables_filter
from tina4_python.Constant import HTTP_OK, HTTP_SERVER_ERROR, TEXT_PLAIN, APPLICATION_JSON
from tina4_python.Template import Template


class UserGroups:
    @staticmethod
    def get_user_group_data():
        """
        Function to get all user group data.
        :return:
        """
        from ..orm.UserGroup import UserGroup

        user_group = UserGroup().select(["id", "name", "permissions"])

        return user_group.to_array()

    @staticmethod
    def get_user_group_data_by_id(user_group_id):
        """
        Function to get all user group data.
        :return:
        """
        from ..orm.UserGroup import UserGroup

        user_group = UserGroup().select(
            ["id", "name", "permissions"],
            "id = ?",
            [str(user_group_id)]
        )

        return user_group

    @staticmethod
    def get_user_group_permission_entries(visible, create, edit, delete):
        """
        Function to return the user group permissions' entries to ensure header, entry sequences.
        :return:
        """
        return {
            "visible": visible,
            "create": create,
            "edit": edit,
            "delete": delete
        }

    @staticmethod
    def get_initial_user_group_permission_list():
        """
        Function to get the initial user group permissions.
        :return:
        """
        return [
            {
                "access_point": "Home",
                "permissions": UserGroups.get_user_group_permission_entries("0", "-", "-", "-"),
                "depends": ""
            },
            {
                "access_point": "Athletes",
                "permissions": UserGroups.get_user_group_permission_entries("0", "0", "-", "0"),
                "depends": ""
            },
            {
                "access_point": "Profile",
                "permissions": UserGroups.get_user_group_permission_entries("0", "-", "0", "-"),
                "depends": "Athletes"
            },
            {
                "access_point": "Videos",
                "permissions": UserGroups.get_user_group_permission_entries("0", "-", "0", "0"),
                "depends": "Profile"
            },
            {
                "access_point": "Links",
                "permissions": UserGroups.get_user_group_permission_entries("0", "0", "-", "0"),
                "depends": "Profile"
            },
            {
                "access_point": "PlayerQ",
                "permissions": UserGroups.get_user_group_permission_entries("0", "0", "-", "-"),
                "depends": "Profile"
            },
            {
                "access_point": "Users",
                "permissions": UserGroups.get_user_group_permission_entries("0", "0", "0", "0"),
                "depends": ""
            },
            {
                "access_point": "User Groups",
                "permissions": UserGroups.get_user_group_permission_entries("0", "0", "0", "0"),
                "depends": ""
            },
            {
                "access_point": "Queue",
                "permissions": UserGroups.get_user_group_permission_entries("0", "-", "0", "0"),
                "depends": ""
            },
            {
                "access_point": "Receptiviti CSV",
                "permissions": UserGroups.get_user_group_permission_entries("0", "-", "-", "-"),
                "depends": ""
            }
        ]

    @staticmethod
    def get_user_group_permissions(user_group):
        """
        Function to return a user group's permissions.
        :param user_group:
        :return:
        """
        if "permissions" in user_group and user_group["permissions"] and user_group["permissions"] != "None":
            return json.loads(user_group["permissions"])

        return UserGroups.get_initial_user_group_permission_list()

    @staticmethod
    def get_access_point_navigation_data(access_point):
        """
        Function to get the relevant access point's navigation data.
        :param access_point:
        :return:
        """
        match access_point:
            case "Home":
                page_url = "/dashboard/home"
                nav_element_id = "homeLink"
            case "Athletes":
                page_url = "/dashboard/athletes/all"
                nav_element_id = "athleteLink"
            case "Users":
                page_url = "/api/users/landing"
                nav_element_id = "usersLink"
            case "User Groups":
                page_url = "/api/user_groups/landing"
                nav_element_id = "userGroupsLink"
            case "Queue":
                page_url = "/dashboard/queue"
                nav_element_id = "queueLink"
            case "Receptiviti CSV":
                page_url = "/api/receptiviti/export"
                nav_element_id = "receptivitiCsvLink"
            case _:
                page_url = ""
                nav_element_id = ""

        return {
            "page_url": page_url,
            "nav_element_id": nav_element_id
        }

    @staticmethod
    def get_holistic_user_group_permission_list(user_group):
        """
        Function to get the holistic user group permissions.
        :return:
        """
        permissions = UserGroups.get_user_group_permissions(user_group[0])

        permissions_list = {}
        authorized = False
        page_url = ""
        nav_element_id = ""

        visible_entries = next((item for item in permissions if item["permissions"]["visible"] == "1"), None)

        if visible_entries:
            authorized = True

            navigation_data = UserGroups.get_access_point_navigation_data(visible_entries["access_point"])

            page_url = navigation_data["page_url"]
            nav_element_id = navigation_data["nav_element_id"]

        for permission in permissions:
            permissions_list[permission["access_point"].replace(" ", "_")] = permission["permissions"]

        user_permissions = {
            "authorized": authorized,
            "landing_page_url": page_url,
            "landing_page_nav_element_id": nav_element_id,
            "permissions": permissions_list
        }

        return user_permissions

    @staticmethod
    def get_user_group_landing(response):
        """
        Function to get the user group landing page
        :param response:
        :return:
        """
        return response(Template.render_twig_template("dashboard/user_groups.twig"))

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

        where = ""

        if data_tables_filter["where"] != "":
            where += " and " + data_tables_filter["where"]

        user_groups = UserGroup().select(["id", "name", "date_created", "permissions", "is_active"],
                                         where,
                                         order_by=data_tables_filter["order_by"],
                                         limit=data_tables_filter["length"],
                                         skip=data_tables_filter["start"])

        data = user_groups.to_paginate()
        data["draw"] = request.params["draw"]

        for user_group in data["data"]:
            permission_string = ""

            for permission in UserGroups.get_user_group_permissions(user_group):
                access_point = permission["access_point"]
                permission_entries = []

                for key, value in permission["permissions"].items():
                    # Skip entirely if value is '-'
                    if str(value) == "-":
                        continue

                    # Determine color based on value
                    color = "bg-success" if str(value) == "1" else "bg-danger"

                    permission_entries.append(
                        f'<div class="mr-3 d-inline-block font-weight-bold text-nowrap" style="font-size: 0.7rem;">'
                        f'<div class="bg-dark d-inline-block text-white text-capitalize py-1 px-2 rounded-left">{key}</div> '
                        f'<div class="{color} d-inline-block text-white text-capitalize py-1 px-2 rounded-right" style="margin-left: -3px;">{value}</div>'
                        f'</div>'
                    )

                # Only add if there are visible permissions
                if permission_entries:
                    permission_string += (
                        f'<div class="text-nowrap my-1">'
                        f'<div style="font-weight: bold; display: inline-block; min-width: 150px;">{access_point}:</div> '
                        f'{"".join(permission_entries)}'
                        f'</div>'
                    )

            user_group["permissions"] = permission_string

        return response(data)

    @staticmethod
    def get_user_groups_form_modal(request, response):
        """
        Function to get a user group form modal.
        :param request:
        :param response:
        :return:
        """
        data = {
            "user_group_permissions": {
                "permissions_list": UserGroups.get_initial_user_group_permission_list()
            }
        }

        id_param = ""
        title = "ADD USER GROUP"

        if "id" in request.params and request.params["id"]:
            from ..orm.UserGroup import UserGroup

            user_group = UserGroup({"id": request.params["id"]})
            user_group.load()

            data["user_group_permissions"]["name"] = user_group.name.value

            if user_group.permissions.value:
                data["user_group_permissions"]["permissions_list"] = user_group.permissions.value

            id_param = str(user_group.id)
            title = "EDIT USER GROUP"

        html = Template.render_twig_template("forms/user_group.twig", data)
        on_click = (f"if ( $('#userGroupModalForm').valid() ) {{ "
                    f"addUserGroup('{id_param}'); $('#formModal').modal('hide');}}")
        form_html = Template.render_twig_template("components/modal_form.twig",
                                                  {"content": html, "title": title, "onclick": on_click})

        return response(form_html)

    @staticmethod
    def post_user_group(request, response):
        """
        Function to add or edit a user
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

        return response(result, HTTP_OK, APPLICATION_JSON)

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

        message = "Failed to delete user group!"
        message_type = "danger"

        if user_group.delete():
            dba.execute("update user set user_group_id = 0 where user_group_id = ?", [request.params["id"]])
            dba.commit()

            message = "User group deleted"
            message_type = "info"

        return response(f"<script>showMessage('{message}', '{message_type}'); userGroupsGrid.ajax.reload();</script>")
