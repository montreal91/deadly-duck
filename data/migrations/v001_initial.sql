--
-- Created December 26, 2025
--
-- @author montreal91
--

CREATE TABLE IF NOT EXISTS game (
    game_id   TEXT PRIMARY KEY NOT NULL,
    object BLOB,
    created_ts INTEGER,
    updated_ts INTEGER
);
