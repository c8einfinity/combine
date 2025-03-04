from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_PLAIN
from tina4_python.Router import get, post, delete

from ..app.Utility import get_data_tables_filter

@get("/api/queue")
async def get_queue(request, response):
    if "draw" not in request.params:
        return response(":(", HTTP_SERVER_ERROR, TEXT_PLAIN)

    from ..orm.Queue import Queue

    data_tables_filter = get_data_tables_filter(request)

    where = ""
    if data_tables_filter["where"]:
        where = f" and {data_tables_filter['where']}"

    queue = Queue().select(
        ["t.*", "CONCAT(player.last_name, ' ', player.first_name) as player"],
        join=f"join player on t.player_id = player.id and t.processed = 0{where}",
        order_by=data_tables_filter["order_by"],
        limit=data_tables_filter["length"],
        skip=data_tables_filter["start"],
    )

    data = queue.to_paginate()

    data["draw"] = request.params["draw"]

    return response(data)

@post("/api/queue/{id}/set_priority")
async def set_queue_priority(request, response):
    """
    Set the priority of a queue item
    :param request:
    :param response:
    :return:
    """

    from ..orm.Queue import Queue

    queue_item = Queue({"id": request.params["id"]})
    queue_item.load()
    queue_item.priority = request.body["priority"]
    if queue_item.save():
        return response({"status": "ok"})

    return response({"status": "error"})

@delete("/api/queue/{id}")
async def delete_queue(request, response):
    """
    Delete a queue item
    :param request:
    :param response:
    :return:
    """

    from ..orm.Queue import Queue

    queue_item = Queue({"id": request.params["id"]})
    if queue_item.delete():
        return response({"status": "ok"})

    return response({"status": "error"})