WITH table_oid as (select CONCAT(schema_name, '.', table_name)::regclass as oid from (select %s as schema_name, %s as table_name) x), 
attrdef AS (
    SELECT
        n.nspname,
        c.relname,
        pg_catalog.array_to_string(c.reloptions || array(select 'toast.' || x from pg_catalog.unnest(tc.reloptions) x), ', ') as relopts,
        c.relpersistence,
        a.attnum,
        a.attname,
        pg_catalog.format_type(a.atttypid, a.atttypmod) as atttype,
        (SELECT substring(pg_catalog.pg_get_expr(d.adbin, d.adrelid, true) for 128) FROM pg_catalog.pg_attrdef d
            WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef) as attdefault,
        a.attnotnull,
        (SELECT c.collname FROM pg_catalog.pg_collation c, pg_catalog.pg_type t
            WHERE c.oid = a.attcollation AND t.oid = a.atttypid AND a.attcollation <> t.typcollation) as attcollation,
        a.attidentity,
        a.attgenerated
    FROM pg_catalog.pg_attribute a
    JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
    JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
    LEFT JOIN pg_catalog.pg_class tc ON (c.reltoastrelid = tc.oid)
    WHERE a.attrelid = (select oid from table_oid limit 1)::regclass
        AND a.attnum > 0
        AND NOT a.attisdropped
    ORDER BY a.attnum
),
coldef AS (
    SELECT
        attrdef.nspname,
        attrdef.relname,
        attrdef.relopts,
        attrdef.relpersistence,
        pg_catalog.format(
            '%I %s%s%s%s%s',
            attrdef.attname,
            attrdef.atttype,
            case when attrdef.attcollation is null then '' else pg_catalog.format(' COLLATE %I', attrdef.attcollation) end,
            case when attrdef.attnotnull then ' NOT NULL' else '' end,
            case when attrdef.attdefault is null then ''
                else case when attrdef.attgenerated = 's' then pg_catalog.format(' GENERATED ALWAYS AS (%s) STORED', attrdef.attdefault)
                    when attrdef.attgenerated <> '' then ' GENERATED AS NOT_IMPLEMENTED'
                    else pg_catalog.format(' DEFAULT %s', attrdef.attdefault)
                end
            end,
            case when attrdef.attidentity<>'' then pg_catalog.format(' GENERATED %s AS IDENTITY',
                    case attrdef.attidentity when 'd' then 'BY DEFAULT' when 'a' then 'ALWAYS' else 'NOT_IMPLEMENTED' end)
                else '' end
        ) as col_create_sql
    FROM attrdef
    ORDER BY attrdef.attnum
),
tabdef AS (
    SELECT
        coldef.nspname,
        coldef.relname,
        coldef.relopts,
        coldef.relpersistence,
        string_agg(coldef.col_create_sql, E',\n    ') as cols_create_sql
    FROM coldef
    GROUP BY
        coldef.nspname, coldef.relname, coldef.relopts, coldef.relpersistence
)
SELECT
    format(
        'CREATE%s TABLE %I.%I%s%s%s;',
        case tabdef.relpersistence when 't' then ' TEMP' when 'u' then ' UNLOGGED' else '' end,
        tabdef.nspname,
        tabdef.relname,
        coalesce(
            (SELECT format(E'\n    PARTITION OF %I.%I %s\n', pn.nspname, pc.relname,
                pg_get_expr(c.relpartbound, c.oid))
                FROM pg_class c JOIN pg_inherits i ON c.oid = i.inhrelid
                JOIN pg_class pc ON pc.oid = i.inhparent
                JOIN pg_namespace pn ON pn.oid = pc.relnamespace
                WHERE c.oid = (select oid from table_oid limit 1)::regclass),
            format(E' (\n    %s\n)', tabdef.cols_create_sql)
        ),
        case when tabdef.relopts <> '' then format(' WITH (%s)', tabdef.relopts) else '' end,
        coalesce(E'\nPARTITION BY '||pg_get_partkeydef((select oid from table_oid limit 1)::regclass), '')
    ) as table_create_sql
FROM tabdef