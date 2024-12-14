WITH rol AS (
    SELECT oid,
            rolname::text AS role_name
        FROM pg_roles
    UNION
    SELECT 0::oid AS oid,
            'public'::text
),
schemas AS ( 
    SELECT oid AS schema_oid,
            n.nspname::text AS schema_name,
            n.nspowner AS owner_oid,
            'schema'::text AS object_type,
            coalesce ( n.nspacl, acldefault ( 'n', n.nspowner ) ) AS acl
        FROM pg_catalog.pg_namespace n
        WHERE n.nspname !~ '^pg_'
            AND n.nspname <> 'information_schema'
),
classes AS ( 
    SELECT schemas.schema_oid,
            schemas.schema_name AS object_schema,
            c.oid,
            c.relname::text AS object_name,
            c.relowner AS owner_oid,
            CASE
                WHEN c.relkind = 'r' THEN 'table'
                WHEN c.relkind = 'v' THEN 'view'
                WHEN c.relkind = 'm' THEN 'materialized view'
                WHEN c.relkind = 'c' THEN 'type'
                WHEN c.relkind = 'i' THEN 'index'
                WHEN c.relkind = 'S' THEN 'sequence'
                WHEN c.relkind = 's' THEN 'special'
                WHEN c.relkind = 't' THEN 'TOAST table'
                WHEN c.relkind = 'f' THEN 'foreign table'
                WHEN c.relkind = 'p' THEN 'partitioned table'
                WHEN c.relkind = 'I' THEN 'partitioned index'
                ELSE c.relkind::text
                END AS object_type,
            CASE
                WHEN c.relkind = 'S' THEN coalesce ( c.relacl, acldefault ( 's', c.relowner ) )
                ELSE coalesce ( c.relacl, acldefault ( 'r', c.relowner ) )
                END AS acl
        FROM pg_class c
        JOIN schemas
            ON ( schemas.schema_oid = c.relnamespace )
        WHERE c.relkind IN ( 'r', 'v', 'm', 'S', 'f', 'p' )
),
cols AS ( 
    SELECT c.object_schema,
            null::integer AS oid,
            c.object_name || '.' || a.attname::text AS object_name,
            'column' AS object_type,
            c.owner_oid,
            coalesce ( a.attacl, acldefault ( 'c', c.owner_oid ) ) AS acl
        FROM pg_attribute a
        JOIN classes c
            ON ( a.attrelid = c.oid )
        WHERE a.attnum > 0
            AND NOT a.attisdropped
),
procs AS (
    SELECT schemas.schema_oid,
            schemas.schema_name AS object_schema,
            p.oid,
            p.proname::text AS object_name,
            p.proowner AS owner_oid,
            CASE p.prokind
                WHEN 'a' THEN 'aggregate'
                WHEN 'w' THEN 'window'
                WHEN 'p' THEN 'procedure'
                ELSE 'function'
                END AS object_type,
            pg_catalog.pg_get_function_arguments ( p.oid ) AS calling_arguments,
            coalesce ( p.proacl, acldefault ( 'f', p.proowner ) ) AS acl
        FROM pg_proc p
        JOIN schemas
            ON ( schemas.schema_oid = p.pronamespace )
),
udts AS (
    SELECT schemas.schema_oid,
            schemas.schema_name AS object_schema,
            t.oid,
            t.typname::text AS object_name,
            t.typowner AS owner_oid,
            CASE t.typtype
                WHEN 'b' THEN 'base type'
                WHEN 'c' THEN 'composite type'
                WHEN 'd' THEN 'domain'
                WHEN 'e' THEN 'enum type'
                WHEN 't' THEN 'pseudo-type'
                WHEN 'r' THEN 'range type'
                WHEN 'm' THEN 'multirange'
                ELSE t.typtype::text
                END AS object_type,
            coalesce ( t.typacl, acldefault ( 'T', t.typowner ) ) AS acl
        FROM pg_type t
        JOIN schemas
            ON ( schemas.schema_oid = t.typnamespace )
        WHERE ( t.typrelid = 0
                OR ( SELECT c.relkind = 'c'
                        FROM pg_catalog.pg_class c
                        WHERE c.oid = t.typrelid ) )
            AND NOT EXISTS (
                SELECT 1
                    FROM pg_catalog.pg_type el
                    WHERE el.oid = t.typelem
                        AND el.typarray = t.oid )
),
fdws AS (
    SELECT null::oid AS schema_oid,
            null::text AS object_schema,
            p.oid,
            p.fdwname::text AS object_name,
            p.fdwowner AS owner_oid,
            'foreign data wrapper' AS object_type,
            coalesce ( p.fdwacl, acldefault ( 'F', p.fdwowner ) ) AS acl
        FROM pg_foreign_data_wrapper p
),
fsrvs AS (
    SELECT null::oid AS schema_oid,
            null::text AS object_schema,
            p.oid,
            p.srvname::text AS object_name,
            p.srvowner AS owner_oid,
            'foreign server' AS object_type,
            coalesce ( p.srvacl, acldefault ( 'S', p.srvowner ) ) AS acl
        FROM pg_foreign_server p
),
all_objects AS (
    SELECT schema_name AS object_schema,
            object_type,
            schema_name AS object_name,
            null::text AS calling_arguments,
            owner_oid,
            acl
        FROM schemas
    UNION
    SELECT object_schema,
            object_type,
            object_name,
            null::text AS calling_arguments,
            owner_oid,
            acl
        FROM classes
    UNION
    SELECT object_schema,
            object_type,
            object_name,
            null::text AS calling_arguments,
            owner_oid,
            acl
        FROM cols
    UNION
    SELECT object_schema,
            object_type,
            object_name,
            calling_arguments,
            owner_oid,
            acl
        FROM procs
    UNION
    SELECT object_schema,
            object_type,
            object_name,
            null::text AS calling_arguments,
            owner_oid,
            acl
        FROM udts
    UNION
    SELECT object_schema,
            object_type,
            object_name,
            null::text AS calling_arguments,
            owner_oid,
            acl
        FROM fdws
    UNION
    SELECT object_schema,
            object_type,
            object_name,
            null::text AS calling_arguments,
            owner_oid,
            acl
        FROM fsrvs
),
acl_base AS (
    SELECT object_schema,
            object_type,
            object_name,
            calling_arguments,
            owner_oid,
            ( aclexplode ( acl ) ).grantor AS grantor_oid,
            ( aclexplode ( acl ) ).grantee AS grantee_oid,
            ( aclexplode ( acl ) ).privilege_type AS privilege_type,
            ( aclexplode ( acl ) ).is_grantable AS is_grantable
        FROM all_objects
)
SELECT 
        acl_base.object_type as "Type",
        acl_base.object_schema as "Schema",
        acl_base.object_name as "Object",
        acl_base.calling_arguments as "Arguments", 
        owner.role_name AS "Owner", 
        acl_base.privilege_type as "Privilege",
        grantor.role_name AS "Granted By",
        acl_base.is_grantable as "With Grant"
    FROM acl_base
    JOIN rol owner
        ON ( owner.oid = acl_base.owner_oid )
    JOIN rol grantor
        ON ( grantor.oid = acl_base.grantor_oid )
    JOIN rol grantee
        ON ( grantee.oid = acl_base.grantee_oid )
    WHERE grantee.role_name = %s 
order by acl_base.object_type, acl_base.object_schema, acl_base.object_name, acl_base.privilege_type