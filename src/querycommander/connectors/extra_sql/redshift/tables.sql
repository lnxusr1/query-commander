select tablename from (
select pg_tables.schemaname, pg_tables.tablename from pg_catalog.pg_tables
join pg_catalog.pg_namespace on pg_tables.schemaname = pg_namespace.nspname
join pg_catalog.pg_class on pg_tables.tablename = pg_class.relname and pg_namespace.oid = pg_class.relnamespace
where pg_class.relkind = 'r' and pg_class.oid not in (select inhrelid from pg_catalog.pg_inherits)
) x where tablename not like 'mv\\_tbl\\_\\_%%\\_\\_%%' and schemaname = %s order by tablename