select 
    grantee as "Role", 
    privilege_type as "Privilege", 
    is_grantable as "With Grant" 
from information_schema.schema_privileges 
where table_schema = %s 
order by grantee, privilege_type