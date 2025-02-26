from tina4_python.Router import get, post, delete

from ..app.Utility import get_data_tables_filter

@get("/api/queue")
async def get_queue(request, response):
    from ..orm.Queue import Queue
    data_tables_filter = get_data_tables_filter(request)

    queue = Queue().select(
        ["t.*", "CONCAT(player.last_name, ' ', player.first_name) as player"],
        join=f"join player on t.player_id = player.id and t.processed = 0 and t.action = 'transcribe'",
        order_by=data_tables_filter["order_by"],
        limit=data_tables_filter["length"],
        skip=data_tables_filter["start"],
    )

    return response(queue.to_paginate())