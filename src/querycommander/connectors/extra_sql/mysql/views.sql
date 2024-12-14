select 
    table_name 
from information_schema.tables 
where table_type = 'VIEW' 
    and table_schema = %s 
order by table_name