select conname as "Constraint Name", pg_class.relname as "Owner", case pg_constraint.contype when 'f' then 'FOREIGN KEY' when 'c' then 'CHECK' when 'u' then 'UNIQUE' when 'p' then 'PRIMARY KEY' else '' end as "Type", pg_get_constraintdef(pg_constraint.oid) as "Expression" from pg_catalog.pg_constraint
join pg_catalog.pg_class on pg_constraint.conrelid = pg_class.oid
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where contype in ('f','p','u') and nspname = %s and pg_class.relname = %s order by conname