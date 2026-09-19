--
-- Created September 19, 2026
--

CREATE TABLE player_assignment (
    game_id TEXT NOT NULL,
    club_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    coach_level INTEGER NOT NULL,
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id, club_id) REFERENCES club(game_id, club_id),
    FOREIGN KEY (game_id, player_id) REFERENCES player(game_id, player_id)
);

CREATE TABLE "contract" (
    game_id TEXT NOT NULL,
    club_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    season_index INTEGER NOT NULL,
    contract_cost INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'future', 'terminated')),
    PRIMARY KEY (game_id, player_id, season_index),
    FOREIGN KEY (game_id, club_id) REFERENCES club(game_id, club_id),
    FOREIGN KEY (game_id, player_id) REFERENCES player(game_id, player_id)
);

CREATE INDEX idx_player_assignment_club_id
    ON player_assignment(game_id, club_id);

CREATE INDEX idx_contract_club_id
    ON "contract"(game_id, club_id);

CREATE UNIQUE INDEX idx_contract_one_active_per_player
    ON "contract"(game_id, player_id)
    WHERE status = 'active';
