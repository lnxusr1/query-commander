select 
    grantee as "Role", 
    privilege_type as "Privileges", 
    grantor as "Granted By", 
    is_grantable as "With Grant" 
from information_schema.table_privileges 
where table_schema = ? 
    and table_name = ? 
order by grantee, privilege_type