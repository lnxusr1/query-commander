select a.attname as "Column Name",
a.attnum as "#", 
pg_catalog.format_type(a.atttypid, a.atttypmod) as "Data Type",
a.attnotnull as "Not Null",
pg_get_expr(d.adbin, d.adrelid) as "Default"
from pg_catalog.pg_attribute a
join pg_catalog.pg_class t on a.attrelid = t.oid
join pg_catalog.pg_namespace ns on t.relnamespace = ns.oid
left join pg_catalog.pg_attrdef d on (a.attrelid, a.attnum) = (d.adrelid, d.adnum)
where a.attnum > 0 and not a.attisdropped
and ns.nspname = %s
and t.relname = %s
order by attnum