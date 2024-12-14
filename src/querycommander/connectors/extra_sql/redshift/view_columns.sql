SELECT 
    a.attname AS column_name,
    a.atttypid::regtype AS data_type,
    a.attnum AS ordinal_position,
    a.attnotnull AS is_nullable
FROM 
    pg_attribute a
JOIN 
    pg_class c ON a.attrelid = c.oid
JOIN 
    pg_namespace n ON c.relnamespace = n.oid
WHERE 
    c.relkind = 'v'  
    AND n.nspname = %s
    AND c.relname = %s
    AND a.attnum > 0 
ORDER BY 
    a.attnum