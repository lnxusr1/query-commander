select CONCAT('CREATE SEQUENCE IF NOT EXISTS ', schemaname, '.', sequencename, '
  INCREMENT BY ', increment_by, '
  MINVALUE ', min_value, '
  MAXVALUE ', max_value, '
  START WITH ', start_value, '
  CACHE ', cache_size, 
case when not cycle then '
  NO CYCLE' else '' end, 
case when owner_table is not null and owner_column is not null then CONCAT('
  OWNED BY ',owner_schema,'.',owner_table,'.',owner_column) else '' end,
';') as definition, pg_sequences.schemaname, pg_sequences.sequencename, pg_sequences.sequenceowner, pg_sequences.last_value, pg_sequences.data_type
from pg_catalog.pg_sequences 
left join (
select seq.relnamespace::regnamespace::text as seq_schema, seq.relname as seq_name,
tab.relnamespace::regnamespace::text as owner_schema, 
tab.relname as owner_table, attr.attname as owner_column
from pg_class as seq
join pg_depend as dep on (seq.relfilenode = dep.objid)
join pg_class as tab on (dep.refobjid = tab.relfilenode)
join pg_attribute as attr on (attr.attnum = dep.refobjsubid and attr.attrelid = dep.refobjid)
) o on pg_sequences.schemaname = seq_schema and pg_sequences.sequencename = seq_name
where schemaname = %s and sequencename = %s