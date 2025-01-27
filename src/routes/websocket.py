from tina4_python.Router import get, post
from tina4_python import Debug

@get("/websocket")
async def index(request, response):
    Debug.info(request)
    pass
