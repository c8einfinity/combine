# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from ..app.UserGroups import UserGroups
from tina4_python.Constant import HTTP_OK, TEXT_HTML
from tina4_python.Router import get, post, delete

@get("/api/user_groups/landing")
async def get_user_group_landing(request, response):
    """
    Route to get the user landing page
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

    return UserGroups.get_user_group_landing(response)

@get("/api/user_groups")
async def get_user_groups(request, response):
    """
    Route to get all the users
    :param request:
    :param response:
    :return:
    """
    return UserGroups.get_user_groups(request, response)

@get("/api/user_groups/form")
async def get_user_group_form(request, response):
    """
    Route to add a user
    :param request:
    :param response:
    :param response:
    :return:
    """
    return UserGroups.get_user_groups_form_modal(request, response)

@post("/api/user_groups")
async def post_user_group(request, response):
    """
    Route to add or edit a user
    :param request:
    :param response:
    :param response:
    :return:
    """
    return UserGroups.post_user_group(request, response)

@delete("/api/user_groups/{id}")
async def delete_user_group(request, response):
    """
    Route to delete a user
    :param request:
    :param response:
    :return:
    """
    return UserGroups.delete_user_group(request, response)
