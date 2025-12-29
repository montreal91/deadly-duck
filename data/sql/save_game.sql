--
-- Created December 27, 2025
--
-- @author montreal91
--
INSERT INTO game (game_id, object, created_ts, updated_ts)
VALUES (:id, :blob, :created_ts, :updated_ts)
ON CONFLICT(game_id) DO UPDATE SET
    object = excluded.object,
    updated_ts  = excluded.updated_ts
;
