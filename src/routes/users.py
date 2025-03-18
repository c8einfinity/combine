# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from tina4_python.Router import get, post, delete
from ..app.Users import Users

@get("api/users/landing")
async def get_users_landing(request, response):
    """
    Route to get the user landing page
    :param request:
    :param response:
    :return:
    """
    return Users.get_users_landing(response)

@get("/api/users")
async def get_users(request, response):
    """
    Route to get all the users
    :param request:
    :param response:
    :return:
    """
    return Users.get_users(request, response)

@post("/api/users")
async def post_users(request, response):
    """
    Route to add a user
    :param request:
    :param response:
    :return:
    """
    return Users.post_users(request, response)

@delete("/api/users/{id}")
async def delete_user(request, response):
    """
    Route to delete a user
    :param request:
    :param response:
    :return:
    """
    return Users.delete_user(request, response)
