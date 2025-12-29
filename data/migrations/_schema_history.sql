--
-- Created December 26, 2025
--
-- @author montreal91
--

CREATE TABLE IF NOT EXISTS schema_migration_history (
    migration_id INTEGER PRIMARY KEY NOT NULL,
    name TEXT,
    filename TEXT NOT NULL,
    applied_at_timestamp INTEGER NOT NULL,
    success INTEGER NOT NULL DEFAULT 1 CHECK (success IN (0, 1))
);
