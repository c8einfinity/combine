
def get_total_transcribed_stats():
    """
    Get the total transcribed video stats
    :return:
    """
    from ..orm.Queue import Queue

    queue = Queue()
    unprocessed_queue = queue.__dba__.fetch_one("select count(*) as unprocessed_count from queue where processed = 0 and action = 'transcribe'")

    processed_queue = queue.__dba__.fetch_one("select count(*) as processed_count from queue where processed = 1 and action = 'transcribe'")

    total_media = queue.__dba__.fetch_one("select count(*) as total_media_count from player_media where media_type = 'video-youtube' and is_deleted = 0 and is_valid = 1")

    valid_media = queue.__dba__.fetch_one("select count(*) as valid_media_count from player_media where media_type = 'video-youtube' and is_deleted = 0 and is_valid = 1 and is_sorted = 1")

    return {
        "unprocessed": unprocessed_queue['unprocessed_count'],
        "processed": processed_queue['processed_count'],
        "total_transcribed": unprocessed_queue['unprocessed_count'] + processed_queue['processed_count'],
        "total_media": total_media['total_media_count'],
        "valid_media": valid_media['valid_media_count']
    }

def get_player_transcribed_stats(player_id):
    """
    Get the transcribed video stats for a player
    :param player_id:
    :return:
    """
    from ..orm.Queue import Queue
    queue = Queue()
    unprocessed_queue = queue.__dba__.fetch_one("select count(*) as unprocessed_count from queue where processed = 0 and action = 'transcribe' and player_id = ?", [player_id])

    processed_queue = queue.__dba__.fetch_one("select count(*) as processed_count from queue where processed = 1 and action = 'transcribe' and player_id = ?", [player_id])

    total_media = queue.__dba__.fetch_one("select count(*) as total_media_count from player_media where media_type = 'video-youtube' and is_deleted = 0 and player_id = ?", [player_id])

    valid_media = queue.__dba__.fetch_one("select count(*) as valid_media_count from player_media where media_type = 'video-youtube' and is_deleted = 0 and is_valid = 1 and player_id = ?", [player_id])

    return {
        "unprocessed": unprocessed_queue['unprocessed_count'] if unprocessed_queue else 0,
        "processed": processed_queue['processed_count'] if processed_queue else 0,
        "total_transcribed": unprocessed_queue['unprocessed_count'] + processed_queue['processed_count'] if unprocessed_queue and processed_queue else 0,
        "total_media": total_media['total_media_count'] if total_media else 0,
        "valid_media": valid_media['valid_media_count'] if valid_media else 0,
    }