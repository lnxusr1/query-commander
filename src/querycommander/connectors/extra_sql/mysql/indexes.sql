SELECT distinct 
    index_name, 
    table_schema, 
    table_name
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = %s and table_name = %s order by index_name
