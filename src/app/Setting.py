
def UpdateInsertSetting(setting_key, setting_value):
    """
    Update or insert a setting in the settings dictionary.

    :param setting: The name of the setting to update or insert.
    :param value: The value to set for the setting.
    """
    from ..orm.AdminSetting import AdminSetting
    existing_setting = AdminSetting().select("*", filter=f"setting_key = '{setting_key}'", limit=1)
    if existing_setting.count > 0:
        # Update the existing setting
        existing_setting.setting_value = setting_value
        saved = existing_setting.save()
    else:
        # Create a new setting
        admin_setting = AdminSetting({"setting_key": setting_key, "setting_value": setting_value})
        saved = admin_setting.save()

    if not saved:
        raise Exception(f"Failed to add or update setting: {setting_key}")

    return saved