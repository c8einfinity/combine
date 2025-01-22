from tina4_python.Template import Template
from tina4_python.Router import get, post
from tina4_python.Swagger import secure
from ..app.Utility import get_data_tables_filter


@get("/api/athletes")
async def get_athletes(request, response):
    from ..orm.Player import Player

    data_tables_filter = get_data_tables_filter(request)

    where = "id <> ?"
    if data_tables_filter["where"] != "":
        where += " and "+data_tables_filter["where"]

    players = Player().select(["first_name", "last_name", "date_of_birth", "sport", "home_town", "major"],
                                where,
                              [0],
                              order_by=data_tables_filter["order_by"],
                              limit=data_tables_filter["length"],
                              skip=data_tables_filter["start"],)

    return response (players.to_paginate())


@post("/api/athletes")
async def post_athletes(request, response):
    from ..orm.Player import Player
    player = Player(request.body)
    player.save()


    return response(player)
