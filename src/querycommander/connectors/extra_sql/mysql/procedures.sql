select 
    specific_name 
from information_schema.routines 
where routine_type = 'PROCEDURE' 
    and routine_schema = %s 
order by specific_name