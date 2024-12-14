select concat(proname, '(', pg_catalog.pg_get_function_identity_arguments(pg_proc.oid)::text, ')') as proname from pg_catalog.pg_proc 
join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid
where nspname = %s and prokind = 'f' order by proname