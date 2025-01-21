from tina4_python.Template import Template
from tina4_python.Router import get, post

@get("/dashboard")
async def index(request, response):


    html = Template.render_twig_template("dashboard.twig")
    return response(html)
