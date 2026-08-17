--
-- Created December 26, 2025
--
-- @author montreal91
--

insert into schema_migration_history
    (migration_id, filename, name, applied_at_timestamp)
values (:migration_id, :filename, :name, :applied_at_timestamp)
;
