from tina4_python.Router import get
from tina4_python.Websocket import Websocket

@get("/websocket/feed")
async def get_websocket(request, response):
    ws = await Websocket(request).connection()
    try:
        while True:
            data = await ws.receive()+ " Reply"
            await ws.send(data)
    except Exception as e:
        pass
    return response("")
