# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from ..app.Users import Users
from tina4_python.Constant import HTTP_OK, TEXT_HTML
from tina4_python.Router import get, post, delete

@get("api/users/landing")
async def get_users_landing(request, response):
    """
    Route to get the user landing page
    :param request:
    :param response:
    :return:
    """
    if not request.session.get('logged_in'):
        return response("<script>window.location.href='/login?s_e=1';</script>", HTTP_OK, TEXT_HTML)

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

@get("/api/users/{id}")
async def get_users_id(request, response):
    """
    Route to get a user by ID
    :param request:
    :param response:
    :return:
    """
    return Users.get_users_id(request, response)

@post("/api/users/{id}")
async def post_users_id(request, response):
    """
    Route to edit a user
    :param request:
    :param response:
    :return:
    """
    return Users.post_users_id(request, response)

@delete("/api/users/{id}")
async def delete_user(request, response):
    """
    Route to delete a user
    :param request:
    :param response:
    :return:
    """
    return Users.delete_user(request, response)
