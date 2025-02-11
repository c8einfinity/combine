alter table player_media add classification text;
CREATE INDEX idx_player_transcripts_player_media_id ON player_transcripts (player_media_id);
