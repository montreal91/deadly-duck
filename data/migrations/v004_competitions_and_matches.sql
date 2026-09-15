--
-- Created August 31, 2026
--
-- @author montreal91
--

CREATE TABLE IF NOT EXISTS competition (
    game_id TEXT NOT NULL,
    competition_id TEXT NOT NULL,
    type TEXT NOT NULL,
    day INTEGER NOT NULL,
    season_index INTEGER NOT NULL,
    is_current INTEGER NOT NULL,
    PRIMARY KEY (game_id, competition_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id)
);

CREATE TABLE IF NOT EXISTS scheduled_match (
    game_id TEXT NOT NULL,
    competition_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    schedule_day INTEGER NOT NULL,
    home_club_id TEXT NOT NULL,
    away_club_id TEXT NOT NULL,
    playoff_series_id TEXT,
    is_played INTEGER NOT NULL,
    PRIMARY KEY (game_id, match_id)
    -- TODO: reimplement the constraints when all model lives in sqlite
--    FOREIGN KEY (game_id, competition_id)
--        REFERENCES competition(game_id, competition_id),
--    FOREIGN KEY (game_id, home_club_id)
--        REFERENCES club(game_id, club_id),
--    FOREIGN KEY (game_id, away_club_id)
--        REFERENCES club(game_id, club_id)
);

CREATE TABLE IF NOT EXISTS match_result (
    game_id TEXT NOT NULL,
    competition_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    home_club_id TEXT NOT NULL,
    away_club_id TEXT NOT NULL,
    home_player_id TEXT,
    away_player_id TEXT,
    home_player_snapshot TEXT,
    away_player_snapshot TEXT,
    home_sets INTEGER NOT NULL,
    away_sets INTEGER NOT NULL,
    home_games INTEGER NOT NULL,
    away_games INTEGER NOT NULL,
    full_score TEXT NOT NULL,
    attendance INTEGER NOT NULL,
    income INTEGER NOT NULL,
    PRIMARY KEY (game_id, match_id),
    FOREIGN KEY (game_id, competition_id)
        REFERENCES competition(game_id, competition_id),
    FOREIGN KEY (game_id, match_id)
        REFERENCES scheduled_match(game_id, match_id),
    FOREIGN KEY (game_id, home_club_id)
        REFERENCES club(game_id, club_id),
    FOREIGN KEY (game_id, away_club_id)
        REFERENCES club(game_id, club_id),
    FOREIGN KEY (game_id, home_player_id)
        REFERENCES player(game_id, player_id),
    FOREIGN KEY (game_id, away_player_id)
        REFERENCES player(game_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_competition_game_id
    ON competition(game_id);

CREATE INDEX IF NOT EXISTS idx_competition_current
    ON competition(game_id, is_current);

CREATE INDEX IF NOT EXISTS idx_scheduled_match_competition_id
    ON scheduled_match(game_id, competition_id);

CREATE INDEX IF NOT EXISTS idx_scheduled_match_day
    ON scheduled_match(game_id, competition_id, schedule_day);

CREATE INDEX IF NOT EXISTS idx_scheduled_match_home_club_id
    ON scheduled_match(game_id, home_club_id);

CREATE INDEX IF NOT EXISTS idx_scheduled_match_away_club_id
    ON scheduled_match(game_id, away_club_id);

CREATE INDEX IF NOT EXISTS idx_match_result_competition_id
    ON match_result(game_id, competition_id);
