select 
    specific_name 
from information_schema.routines 
where routine_type = 'FUNCTION'
    and routine_schema = %s 
order by specific_name