# Copyright 2025 Code Infinity
# Author: Jacques van Zuydam <jacques@codeinfinity.co.za>
# Author: Chanelle Bösiger <chanelle@codeinfinity.co.za>

from ..app.MiddleWare import MiddleWare
from tina4_python.Template import Template
from tina4_python.Router import get, post, delete, middleware

@middleware(MiddleWare, ["before_route_session_validation"])
@get("/settings")
async def settings_get(request, response):
    """
    Handle GET requests to the /settings endpoint.
    """
    from ..orm.Sport import Sport
    from ..orm.AdminSetting import AdminSetting

    sports = Sport().select("*", limit=100, order_by="name")

    admin_settings = AdminSetting().select("*", limit=100, order_by="setting_key")
    admin_settings = admin_settings.to_list()
    # map the admin settings to a dictionary for easier access
    mapped_admin_settings = {setting["setting_key"]: setting["setting_value"] for setting in admin_settings}

    html = Template.render_twig_template("admin_settings.twig", data={"sports": sports, "admin_settings": mapped_admin_settings})

    return response(html)

@middleware(MiddleWare, ["before_route_session_validation"])
@post("/settings/add-update-search-parameters")
async def add_update_search_parameters(request, response):
    """
    Handle POST requests to add sport search parameters.
    """
    from ..orm.AdminSetting import AdminSetting
    from ..app.Setting import UpdateInsertSetting

    if request.body["defaultVideoSportSearchParameters"]:
        current_default = AdminSetting().select("*", filter="setting_key = 'video_sport_search_parameters'", limit=1)
        video_default = AdminSetting({"id": current_default[0]["id"]})
        video_default.load()

        video_default.setting_value = request.body["defaultVideoSportSearchParameters"]
        video_default.save()

    if request.body["defaultBiographySportSearchParameters"]:
        current_default = AdminSetting().select("*", filter="setting_key = 'bio_sport_search_parameters'", limit=1)
        bio_default = AdminSetting({"id": current_default[0]["id"]})
        bio_default.load()

        bio_default.setting_value = request.body["defaultBiographySportSearchParameters"]
        bio_default.save()

    if request.body["videoSportSearchRequest"] and request.body["videoSportSearchRequestSport"]:
        setting_key = f"video_sport_{request.body["videoSportSearchRequestSport"]}_search_parameters"
        setting_value = request.body["videoSportSearchRequest"]

        try:
            saved = UpdateInsertSetting(setting_key, setting_value)
        except Exception as e:
            return response({"error": str(e)}, status=500)

        if not saved:
            return response({"error": "Failed to add or update sport search parameter"}, status=500)

    if request.body["bioSportSearchRequest"] and request.body["bioSportSearchRequestSport"]:
        setting_key = f"bio_sport_{request.body['bioSportSearchRequestSport']}_search_parameters"
        setting_value = request.body["bioSportSearchRequest"]

        try:
            saved = UpdateInsertSetting(setting_key, setting_value)
        except Exception as e:
            return response({"error": str(e)}, status=500)

        if not saved:
            return response({"error": "Failed to add or update sport search parameter"}, status=500)

    return response({"message": "Sport search parameter added successfully"})

@middleware(MiddleWare, ["before_route_session_validation"])
@post("/setting/update/{setting_key}")
async def update_setting(request, response):
    """
    Handle POST requests to update a setting.
    """
    from ..orm.AdminSetting import AdminSetting

    if not request.params["setting_key"] or not request.body["setting_value"]:
        return response({"error": "Setting key and value are required"}, status=400)

    current_setting = AdminSetting().select("*", filter=f"setting_key = '{request.params['setting_key']}'", limit=1)

    if current_setting.count == 0:
        return response({"error": "Setting not found"}, status=404)

    setting = AdminSetting({"id": current_setting[0]["id"]})
    setting.load()

    setting.setting_value = request.body["setting_value"]
    saved = setting.save()

    if not saved:
        return response({"error": "Failed to update setting"}, status=500)

    return response({"message": "Setting updated successfully"})

@middleware(MiddleWare, ["before_route_session_validation"])
@delete("/setting/delete/{setting_key}")
async def delete_setting(request, response):
    """
    Handle POST requests to delete a setting.
    """
    from ..orm.AdminSetting import AdminSetting

    if not request.params["setting_key"]:
        return response({"error": "Setting key is required"}, status=400)

    setting = AdminSetting().select("*", filter=f"setting_key = '{request.params["setting_key"]}'", limit=1)

    if setting.count == 0:
        return response({"error": "Setting not found"}, status=404)

    setting = AdminSetting({"id": setting[0]["id"]})
    deleted = setting.delete()

    if not deleted:
        return response({"error": "Failed to delete setting"}, status=500)

    return response({"message": "Setting deleted successfully"})
