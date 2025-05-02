
def get_total_transcribed_stats():
    """
    Get the total transcribed video stats
    :return:
    """
    from .. import dba

    untranscribed_media = dba.fetch_one('select count(*) as untranscribed_count from player_transcripts where '
                                        'cast(data as char) like \'{"transcription": [[]%\' group by player_media_id')

    speaker_verified = dba.fetch_one("select count(*) as speaker_verified_count from player_transcripts where "
                                     "verified_user_id > 0")

    total_media = dba.fetch_one("select count(*) as total_media_count from player_media where media_type = "
                                "'video-youtube' and is_deleted = 0 and is_valid = 1")

    valid_media = dba.fetch_one("select count(*) as valid_media_count from player_media where media_type = "
                                "'video-youtube' and is_deleted = 0 and is_valid = 1 and is_sorted = 1")

    reports_sent = dba.fetch_one("select count(distinct player_id) as reports_sent_count from player_result")

    incomplete_bios = dba.fetch_one("select count(*) as incomplete_bios_count from player where "
                                    "image is null or first_name = '' or last_name = '' or sport = '' or position = "
                                    "'' or date_of_birth is null or home_town = '' or team = ''")
    incomplete_player_bios = None

    if incomplete_bios["incomplete_bios_count"] > 0:
        # get the first 10 incomplete bios
        incomplete_player_bios = dba.fetch("select id, first_name, last_name from player where "
                                        "image is null or first_name = '' or last_name = '' or sport = '' or position = '' or date_of_birth is null or home_town = '' or team = ''")

    dba.close()

    return {
        "untranscribed": untranscribed_media['untranscribed_count'],
        "processed": speaker_verified['speaker_verified_count'],
        "total_transcribed": total_media['total_media_count'] - untranscribed_media['untranscribed_count'],
        "total_media": total_media['total_media_count'],
        "valid_media": valid_media['valid_media_count'],
        "reports_sent": reports_sent['reports_sent_count'],
        "incomplete_bios": incomplete_bios['incomplete_bios_count'],
        "incomplete_player_bios": incomplete_player_bios
    }

def get_player_transcribed_stats(player_id):
    """
    Get the transcribed video stats for a player
    :param player_id:
    :return:
    """
    from .. import dba

    unprocessed_queue = dba.fetch_one("select count(*) as unprocessed_count from queue where processed = 0 and action = 'transcribe' and player_id = ?", [player_id])

    processed_queue = dba.fetch_one("select count(*) as processed_count from player_transcripts where player_id = ? and verified_user_id > 0", [player_id])

    total_media = dba.fetch_one("select count(*) as total_media_count from player_media where media_type = 'video-youtube' and is_deleted = 0 and player_id = ?", [player_id])

    valid_media = dba.fetch_one("select count(*) as valid_media_count from player_media where media_type = 'video-youtube' and is_deleted = 0 and is_valid = 1 and is_sorted = 1 and player_id = ?", [player_id])

    dba.close()

    return {
        "unprocessed": unprocessed_queue['unprocessed_count'] if unprocessed_queue else 0,
        "processed": processed_queue['processed_count'] if processed_queue else 0,
        "total_transcribed": unprocessed_queue['unprocessed_count'] + processed_queue['processed_count'] if unprocessed_queue and processed_queue else 0,
        "total_media": total_media['total_media_count'] if total_media else 0,
        "valid_media": valid_media['valid_media_count'] if valid_media else 0,
    }