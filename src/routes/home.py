from tina4_python.Router import get

@get("/")
async def index(request, response):
    request.session.set("logged_in", True)
    return response("Ok")

print("OK")