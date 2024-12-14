select part.relname as partname from pg_catalog.pg_class base_part
join pg_catalog.pg_inherits i on i.inhparent = base_part.oid
join pg_catalog.pg_class part on part.oid = i.inhrelid
where base_part.relnamespace::regnamespace::text = %s and base_part.relname = %s and part.relkind in ('r','p')
order by part.relname