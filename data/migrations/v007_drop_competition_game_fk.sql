--
-- Created September 14, 2026
--
-- @author montreal91
--

DROP TABLE competition;
-- TODO: Add foreign key game_id -> game table when the start_game_system will be implemented
CREATE TABLE competition (
    game_id TEXT NOT NULL,
    competition_id TEXT NOT NULL,
    type TEXT NOT NULL,
    day INTEGER NOT NULL,
    season_index INTEGER NOT NULL,
    is_over INTEGER NOT NULL,
    object BLOB,
    PRIMARY KEY (game_id, competition_id)
);

CREATE INDEX IF NOT EXISTS idx_competition_game_id
    ON competition(game_id);

CREATE INDEX IF NOT EXISTS idx_competition_is_over
    ON competition(game_id, is_over);
