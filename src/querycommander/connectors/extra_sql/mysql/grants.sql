select 
    grantee as "Role", 
    privilege_type as "Privilege", 
    is_grantable as "With Grant"
from information_schema.table_privileges 
where table_schema = %s 
    and table_name in ('global_priv',%s)
order by grantee, privilege_type, is_grantable