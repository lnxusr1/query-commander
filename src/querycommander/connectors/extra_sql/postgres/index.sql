select CONCAT(pg_get_indexdef(indexrelid),';') as definition
from pg_catalog.pg_index
join pg_catalog.pg_class on pg_index.indexrelid = pg_class.oid
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where nspname = %s and relname = %s;