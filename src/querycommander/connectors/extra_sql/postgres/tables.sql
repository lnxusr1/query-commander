select tablename from (
select nspname as schemaname, relname as tablename from pg_catalog.pg_class
join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid
where pg_class.oid in (select partrelid from pg_catalog.pg_partitioned_table)
and pg_class.oid not in (select inhrelid from pg_catalog.pg_inherits)
union
select pg_tables.schemaname, pg_tables.tablename from pg_catalog.pg_tables
join pg_catalog.pg_namespace on pg_tables.schemaname = pg_namespace.nspname
join pg_catalog.pg_class on pg_tables.tablename = pg_class.relname and pg_namespace.oid = pg_class.relnamespace
where pg_class.oid not in (select partrelid from pg_catalog.pg_partitioned_table)
and pg_class.oid not in (select inhrelid from pg_catalog.pg_inherits)
) x where schemaname = %s order by tablename