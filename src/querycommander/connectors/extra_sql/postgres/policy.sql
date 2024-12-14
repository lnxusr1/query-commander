select CONCAT('CREATE POLICY ', polname, chr(10), '    ON ',
nspname, '.', 
relname, chr(10), '    AS ',
case when polpermissive then 'PERMISSIVE' else 'RESTRICTIVE' end, chr(10), '    FOR ',
case polcmd
when 'r' then 'SELECT'
when 'a' then 'INSERT'
when 'w' then 'UPDATE'
when 'd' then 'DELETE'
when '*' then 'ALL'
else null
end, chr(10), '    TO ',
array_to_string(case 
when polroles = '{0}'::oid[] then string_to_array('public', '')::name[]
else array(
select rolname from pg_catalog.pg_roles where oid = ANY(polroles) order by rolname
) end,', '), chr(10), '    USING (',
pg_catalog.pg_get_expr(polqual, polrelid, false), ')',
case when polwithcheck is not null then CONCAT(chr(10), '    WITH CHECK (',
pg_catalog.pg_get_expr(polwithcheck, polrelid, false), ')') else '' end,
';') as definition
from pg_catalog.pg_policy
join pg_catalog.pg_class on pg_policy.polrelid = pg_class.oid
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where nspname::text = %s and relname::text = %s and polname::text = %s