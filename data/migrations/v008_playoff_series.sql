--
-- Created September 15, 2026
--
-- @author montreal91
--

CREATE TABLE IF NOT EXISTS playoff_series (
    game_id TEXT NOT NULL,
    competition_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    position INTEGER NOT NULL,
    top_club_id TEXT,
    bottom_club_id TEXT,
    PRIMARY KEY (game_id, series_id),
    UNIQUE (game_id, competition_id, round_number, position),
    FOREIGN KEY (game_id, competition_id)
        REFERENCES competition(game_id, competition_id),
    FOREIGN KEY (game_id, top_club_id)
        REFERENCES club(game_id, club_id),
    FOREIGN KEY (game_id, bottom_club_id)
        REFERENCES club(game_id, club_id)
);

CREATE INDEX IF NOT EXISTS idx_playoff_series_competition_id
    ON playoff_series(game_id, competition_id);

CREATE INDEX IF NOT EXISTS idx_playoff_series_round
    ON playoff_series(game_id, competition_id, round_number);
