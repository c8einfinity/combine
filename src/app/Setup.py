import json

from tina4_python import tina4_auth
from tina4_python import Debug
from .Scraper import get_youtube_videos

def check_setup(dba):
    from ..orm.User import User
    # check for an admin user
    user = User()

    if not user.load("is_active = ? and user_group_id = ?", [1, 1]):
        Debug.error("Admin user already exists")
        user.first_name = "Admin"
        user.last_name = "Admin"
        user.email = "admin@qfinder.io"
        user.password = tina4_auth.hash_password("QFinder1234!")
        user.is_active = 1
        user.user_group_id = 1
        user.save()
    else:
        Debug.info("Admin user already exists")


def check_players(filter=""):
    from ..orm.Player import Player
    from ..orm.PlayerMedia import PlayerMedia

    try:
        players = Player().select(limit=1000, filter=filter)

        for player_info in players.to_list():
            Debug.info("Player", player_info)
            player = Player(player_info)

            if player.last_name == "":
                player_name = str(player.first_name).split(" ", 1)
                player.first_name = player_name[0]
                player.last_name = player_name[1]
                player.save()

            if player.is_video_links_created == 0:
                you_tube_links = get_youtube_videos(str(player.first_name)+" "+str(player.last_name))
                for you_tube_link in you_tube_links:
                    player_media = PlayerMedia()
                    player_media.url = you_tube_link["url"]
                    player_media.player_id = player.id
                    player_media.media_type = 'video-youtube'
                    player_media.is_valid = 1
                    player_media.metadata = you_tube_link["metadata"]
                    player_media.save()

                player.is_video_links_created = 1
                player.save()
    except Exception as e:
        print(str(e))
