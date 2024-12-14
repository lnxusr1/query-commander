select CONCAT(trim(pg_catalog.pg_get_functiondef(pg_proc.oid)::text), ';') as definition, nspname, proname, proowner::regrole::text as ownername, pg_language.lanname, pg_catalog.pg_get_function_identity_arguments(pg_proc.oid) as arguments
from pg_catalog.pg_proc
join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid
left join pg_catalog.pg_language on pg_proc.prolang = pg_language.oid
where nspname = %s and CONCAT(proname, '(', pg_catalog.pg_get_function_identity_arguments(pg_proc.oid), ')') = %s