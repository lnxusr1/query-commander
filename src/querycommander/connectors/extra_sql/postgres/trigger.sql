select CONCAT(trim(pg_catalog.pg_get_triggerdef(pg_trigger.oid)), ';') as definition
from pg_catalog.pg_trigger
join pg_catalog.pg_class on pg_trigger.tgrelid = pg_class.oid
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where nspname = %s and relname = %s and tgname = %s