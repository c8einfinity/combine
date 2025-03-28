ALTER TABLE player_transcripts RENAME COLUMN user_verified_speaker TO verified_user_id;
ALTER TABLE player_transcripts ADD COLUMN verified_at TIMESTAMP DEFAULT NULL;