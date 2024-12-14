select pg_catalog.pg_get_functiondef(pg_proc.oid) from pg_catalog.pg_proc 
join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid
where nspname = %s AND proname not like 'mv\\_sp\\_\\_%%\\_\\_%%' 
and proname = %s