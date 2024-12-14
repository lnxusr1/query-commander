select * from (
    select distinct 
        constraint_name, 
        constraint_schema, 
        table_name 
    from information_schema.referential_constraints
    union all
    select 
        constraint_name, 
        table_schema as constraint_schema, 
        table_name 
    from information_schema.table_constraints 
    where constraint_type != 'CHECK'
) constraints 
where constraint_schema = %s 
    and table_name = %s
order by constraint_name