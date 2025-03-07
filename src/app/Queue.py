
def get_total_transcribed_stats():
    """
    Get the total transcribed video stats
    :return:
    """
    from ..orm.Queue import Queue

    queue = Queue()
    unprocessed_queue = queue.__dba__.fetch("select count(*) as unprocessed_count from queue where processed = 0 and action = 'transcribe'")

    processed_queue = queue.__dba__.fetch("select count(*) as processed_count from queue where processed = 1 and action = 'transcribe'")

    total_media = queue.__dba__.fetch("select count(*) as total_media from player_media where media_type = 'video-youtube' and is_deleted = 0")

    valid_media = queue.__dba__.fetch("select count(*) as valid_media from player_media where media_type = 'video-youtube' and is_deleted = 0 and is_valid = 1")

    return {"unprocessed": unprocessed_queue[0], "processed": processed_queue[0], "total_media": total_media[0], "valid_media": valid_media[0]}

def get_player_transcribed_stats(player_id):
    """
    Get the transcribed video stats for a player
    :param player_id:
    :return:
    """
    from ..orm.Queue import Queue
    from ..orm.PlayerMedia import PlayerMedia

    unprocessed_queue = Queue()

    processed_queue = Queue({"player_id": player_id, "type": "transcribe", "processed": 1})
    processed_queue.select("sum(processed) as processed_count")

    return {}