# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from ..app.UserGroup import UserGroup
from ..app.Utility import get_data_tables_filter
from tina4_python import tina4_auth
from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_PLAIN
from tina4_python.Template import Template

class Users:
    @staticmethod
    def get_users_landing(response):
        """
        Function to get the user landing page
        :param response:
        :return:
        """
        data = {
            "user_groups": UserGroup.get_user_group_data()
        }

        return response(Template.render_twig_template("dashboard/users.twig", data))

    @staticmethod
    def get_users(request, response):
        """
        Function to get all the users
        :param request:
        :param response:
        :return:
        """
        if "draw" not in request.params:
            return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

        from ..orm.User import User

        data_tables_filter = get_data_tables_filter(request)

        where = "id <> ?"

        if data_tables_filter["where"] != "":
            where += " and " + data_tables_filter["where"]

        users = User().select(["id", "first_name", "last_name", "email", "date_created", "user_group_id", "is_active"],
                              where,
                              [0],
                              order_by=data_tables_filter["order_by"],
                              limit=data_tables_filter["length"],
                              skip=data_tables_filter["start"])

        data = users.to_paginate()
        data["draw"] = request.params["draw"]

        return response(data)

    @staticmethod
    def post_users(request, response):
        """
        Function to add a user
        :param request:
        :param response:
        :return:
        """
        from ..orm.User import User

        request.body["password"] = tina4_auth.hash_password(request.body["password"])

        user = User(request.body)
        user.save()

        return response(user)

    @staticmethod
    def get_users_id(request, response):
        from ..orm.User import User

        user = User({"id": request.params["id"]})
        user.load()

        data = {
            "user": user.to_dict(),
            "user_groups": UserGroup.get_user_group_data()
        }

        html = Template.render_twig_template("forms/edit_user.twig", data)
        title = "EDIT USER"
        on_click = (f"if ( $('#usersModalForm').valid() ) {{ "
                    f"saveForm('usersModalForm', '/api/users/{str(user.id)}', 'message'); "
                    f"$('#formModal').modal('hide');}}")

        form_html = Template.render_twig_template("components/modal_form.twig",
                                                  {"content": html, "title": title, "onclick": on_click})

        return response(form_html)

    @staticmethod
    def post_users_id(request, response):
        """
        Function to edit a user
        :param request:
        :param response:
        :return:
        """
        from ..orm.User import User

        user = User({"id": request.body["id"]})

        if user.save():
            return response("User saved")
        else:
            return response("Failed to save user!")

    @staticmethod
    def delete_user(request, response):
        """
        Function to delete a user
        :param request:
        :param response:
        :return:
        """
        from ..orm.User import User

        user = User({"id": request.params["id"]})

        if user.delete():
            return response("User deleted")
        else:
            return response("Failed to delete user!")
