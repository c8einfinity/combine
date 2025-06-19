from tina4_python import Debug
from tina4_python.Constant import HTTP_SERVER_ERROR, TEXT_HTML, TEXT_PLAIN, HTTP_OK, HTTP_NOT_FOUND
from tina4_python.Template import Template
from tina4_python.Router import get, post, delete

@get("/settings")
def settings_get(request, response):
    """
    Handle GET requests to the /settings endpoint.
    """
    html = Template.render_twig_template("settings.twig", data={})

    return response(html)