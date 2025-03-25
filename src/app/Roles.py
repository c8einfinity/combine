class Roles:
    @staticmethod
    def get_initial_roles_permission_list():
        """
        Function to get the initial roles.
        :return:
        """
        headers = [
            "visible",
            "create",
            "edit",
            "delete"
        ]

        access_list = [
            {
                "access_point": "Overview",
                "permissions": {
                    "visible": "0",
                    "create": "-",
                    "edit": "-",
                    "delete": "-"
                }
            },
            {
                "access_point": "Athletes",
                "permissions": {
                    "visible": "0",
                    "create": "0",
                    "edit": "-",
                    "delete": "0"
                }
            },
            {
                "access_point": "Profile",
                "permissions": {
                    "visible": "0",
                    "create": "-",
                    "edit": "-",
                    "delete": "-"
                }
            },
            {
                "access_point": "Videos",
                "permissions": {
                    "visible": "0",
                    "create": "-",
                    "edit": "-",
                    "delete": "0"
                }
            },
            {
                "access_point": "Links",
                "permissions": {
                    "visible": "0",
                    "create": "0",
                    "edit": "-",
                    "delete": "0"
                }
            },
            {
                "access_point": "PlayerQ",
                "permissions": {
                    "visible": "0",
                    "create": "-",
                    "edit": "0",
                    "delete": "-"
                }
            },
            {
                "access_point": "Users",
                "permissions": {
                    "visible": "0",
                    "create": "0",
                    "edit": "0",
                    "delete": "0"
                }
            },
            {
                "access_point": "User Groups",
                "permissions": {
                    "visible": "0",
                    "create": "0",
                    "edit": "0",
                    "delete": "0"
                }
            },
            {
                "access_point": "Queue",
                "permissions": {
                    "visible": "0",
                    "create": "-",
                    "edit": "0",
                    "delete": "0"
                }
            }
        ]

        return {
            "access_list": access_list,
            "headers": headers
        }
