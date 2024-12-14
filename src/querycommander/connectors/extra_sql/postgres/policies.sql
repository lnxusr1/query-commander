select polname from pg_catalog.pg_policy
join pg_catalog.pg_class on pg_policy.polrelid = pg_class.oid
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where nspname = %s and relname = %s
order by polname