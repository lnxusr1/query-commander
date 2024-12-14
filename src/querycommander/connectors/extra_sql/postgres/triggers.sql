select tgname from pg_catalog.pg_trigger
join pg_catalog.pg_class on pg_trigger.tgrelid = pg_class.oid
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where not tgisinternal and nspname = %s and pg_class.relname = %s
order by tgname