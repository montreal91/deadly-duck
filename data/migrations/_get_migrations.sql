--
-- Created December 26, 2025
--
-- @author montreal91
--

select migration_id
from schema_migration_history
order by applied_at_timestamp
;
