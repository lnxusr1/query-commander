select 
    table_schema, 
    table_name, 
    table_collation, 
    engine, 
    table_type 
from information_schema.tables 
where table_schema = %s 
    and table_name = %s