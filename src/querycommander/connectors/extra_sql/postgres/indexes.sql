select i.relname as "Index Name", case when pg_index.indisunique = 't' then true else false end as "Unique", CONCAT(pg_get_indexdef(indexrelid),';') as "Expression" 
from pg_catalog.pg_index
join pg_catalog.pg_class t on pg_index.indrelid = t.oid
join pg_catalog.pg_namespace on t.relnamespace = pg_namespace.oid
join pg_catalog.pg_class i on pg_index.indexrelid = i.oid
where not indisprimary and nspname = %s and t.relname = %s
order by i.relname