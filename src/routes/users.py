# Copyright 2025 Code Infinity
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from ..app.MiddleWare import MiddleWare
from ..app.Users import Users
from tina4_python.Router import get, post, delete, middleware

@middleware(MiddleWare)
@get("api/users/landing")
async def get_users_landing(request, response):
    """
    Route to get the user landing page
    :param request:
    :param response:
    :return:
    """
    return Users.get_users_landing(response)

@middleware(MiddleWare)
@get("/api/users")
async def get_users(request, response):
    """
    Route to get all the users
    :param request:
    :param response:
    :return:
    """
    return Users.get_users(request, response)

@middleware(MiddleWare)
@post("/api/users")
async def post_users(request, response):
    """
    Route to add a user
    :param request:
    :param response:
    :return:
    """
    return Users.post_users(request, response)

@middleware(MiddleWare)
@get("/api/users/{id}")
async def get_users_id(request, response):
    """
    Route to get a user by ID
    :param request:
    :param response:
    :return:
    """
    return Users.get_users_id(request, response)

@middleware(MiddleWare)
@post("/api/users/{id}")
async def post_users_id(request, response):
    """
    Route to edit a user
    :param request:
    :param response:
    :return:
    """
    return Users.post_users_id(request, response)

@middleware(MiddleWare)
@delete("/api/users/{id}")
async def delete_user(request, response):
    """
    Route to delete a user
    :param request:
    :param response:
    :return:
    """
    return Users.delete_user(request, response)
