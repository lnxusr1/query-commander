select relname from pg_catalog.pg_class
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where pg_class.relkind = 'S' and nspname = %s
order by relname