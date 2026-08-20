--
-- Created August 18, 2026
--
-- @author montreal91
--

CREATE TABLE IF NOT EXISTS player (
    game_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    first_name TEXT NOT NULL,
    second_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    technique INTEGER NOT NULL,
    endurance INTEGER NOT NULL,
    exhaustion INTEGER NOT NULL,
    experience INTEGER NOT NULL,
    current_stamina INTEGER NOT NULL,
    reputation INTEGER NOT NULL,
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id)
);

CREATE TABLE IF NOT EXISTS club (
    game_id TEXT NOT NULL,
    club_id TEXT NOT NULL,
    name TEXT NOT NULL,
    country TEXT,
    city TEXT,
    balance INTEGER NOT NULL,
    coach_power INTEGER NOT NULL,
    selected_player_id TEXT,
    PRIMARY KEY (game_id, club_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id),
    FOREIGN KEY (game_id, selected_player_id) REFERENCES player(game_id, player_id)
);

CREATE TABLE IF NOT EXISTS roster_entry (
    game_id TEXT NOT NULL,
    club_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    coach_level INTEGER NOT NULL,
    contract_cost INTEGER NOT NULL,
    has_next_contract INTEGER NOT NULL,
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id, player_id) REFERENCES player(game_id, player_id),
    FOREIGN KEY (game_id, club_id) REFERENCES club(game_id, club_id)
);

CREATE INDEX IF NOT EXISTS idx_club_game_id
    ON club(game_id);

CREATE INDEX IF NOT EXISTS idx_player_game_id
    ON player(game_id);

CREATE INDEX IF NOT EXISTS idx_roster_entry_game_id
    ON roster_entry(game_id);

CREATE INDEX IF NOT EXISTS idx_roster_entry_club_id
    ON roster_entry(game_id, club_id);
