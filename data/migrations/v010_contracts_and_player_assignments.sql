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
    contract_cost INTEGER NOT NULL,
    has_next_contract INTEGER NOT NULL CHECK (has_next_contract IN (0, 1)),
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id, club_id) REFERENCES club(game_id, club_id),
    FOREIGN KEY (game_id, player_id) REFERENCES player(game_id, player_id)
);

CREATE INDEX idx_player_assignment_club_id
    ON player_assignment(game_id, club_id);

CREATE INDEX idx_contract_club_id
    ON "contract"(game_id, club_id);
