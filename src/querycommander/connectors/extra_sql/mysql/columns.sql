select 
    column_name 
from information_schema.columns 
where table_schema = %s 
    and table_name = %s 
order by ordinal_position