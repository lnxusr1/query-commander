select CONCAT('ALTER TABLE ', pg_namespace.nspname, '.', pg_class.relname, ' ADD CONSTRAINT ', conname, ' ', pg_get_constraintdef(pg_constraint.oid), ';') as definition
from pg_catalog.pg_constraint
join pg_catalog.pg_namespace on pg_constraint.connamespace = pg_namespace.oid
join pg_catalog.pg_class on pg_constraint.conrelid = pg_class.oid
join pg_catalog.pg_namespace rns on pg_class.relnamespace = rns.oid
where pg_namespace.nspname = %s and conname = %s;