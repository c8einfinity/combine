from tina4_python.Template import Template
from tina4_python.Router import get, post

@get("/dashboard")
async def get_dashboard(request, response):


    html = Template.render_twig_template("dashboard.twig")
    return response(html)


@get("/dashboard/athletes")
async def get_dashboard_athletes(request, response):

    html = Template.render_twig_template("dashboard/athletes.twig")

    return response(html)
