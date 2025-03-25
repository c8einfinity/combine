# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from tina4_python.Router import get, post, delete
from ..app.UserGroup import UserGroup

@get("/api/user_groups/landing")
async def get_user_group_landing(request, response):
    """
    Route to get the user landing page
    :param request:
    :param response:
    :return:
    """
    return UserGroup.get_user_group_landing(response)

@get("/api/user_groups")
async def get_user_groups(request, response):
    """
    Route to get all the users
    :param request:
    :param response:
    :return:
    """
    return UserGroup.get_user_groups(request, response)

@post("/api/user_groups")
async def post_user_group(request, response):
    """
    Route to add a user
    :param request:
    :param response:
    :return:
    """
    return UserGroup.post_user_group(request, response)

@delete("/api/user_groups/{id}")
async def delete_user_group(request, response):
    """
    Route to delete a user
    :param request:
    :param response:
    :return:
    """
    return UserGroup.delete_user_group(request, response)
