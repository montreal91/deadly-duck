--
-- Created September 14, 2026
--
-- @author montreal91
--

ALTER TABLE competition
RENAME COLUMN is_current TO is_over;

DROP INDEX IF EXISTS idx_competition_current;

CREATE INDEX IF NOT EXISTS idx_competition_is_over
    ON competition(game_id, is_over);
