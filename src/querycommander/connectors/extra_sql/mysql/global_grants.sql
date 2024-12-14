select 
    grantee as "Role", 
    privilege_type as "Privilege", 
    is_grantable as "With Grant" 
from information_schema.user_privileges 
order by grantee, privilege_type, is_grantable