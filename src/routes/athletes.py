from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_HTML, TEXT_PLAIN, HTTP_OK
from tina4_python.Template import Template
from tina4_python.Router import get, post
from tina4_python.Swagger import secure
from ..app.Utility import get_data_tables_filter


@get("/api/athletes")
async def get_athletes(request, response):
    if "draw" not in request.params:
        return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

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

    data = players.to_paginate()

    data["draw"] = request.params["draw"]

    return response (data)


@post("/api/athletes")
async def post_athletes(request, response):
    from ..orm.Player import Player
    player = Player(request.body)
    player.save()


    return response(player)
