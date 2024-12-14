select 
    CONCAT(
        'CREATE ROLE ', rolname, ' WITH',
        case when rolsuper = 't' then CONCAT(chr(10), '    SUPERUSER') else '' end,
        case when rolcreatedb = 't' then CONCAT(chr(10), '    CREATEDB') else '' end,
        case when rolcreaterole = 't' then CONCAT(chr(10), '    CREATEROLE') else '' end,
        case when rolinherit = 'f' then CONCAT(chr(10), '    NOINHERIT') else '' end,
        case when rolcanlogin = 't' then CONCAT(chr(10), '    LOGIN') else '' end,
        case when rolreplication = 't' then CONCAT(chr(10), '    REPLICATION') else '' end,
        case when rolbypassrls = 't' then CONCAT(chr(10), '    BYPASSRLS') else '' end,
        case when rolvaliduntil is not null then CONCAT(chr(10), '    VALID UNTIL ', cast(rolvaliduntil as text)) else '' end,
        case when rolconnlimit is not null then CONCAT(chr(10), '    CONNECTION LIMIT ', cast(rolconnlimit as text)) else '' end,
        ';'
    ) as definition,
    rolname, 
    case when rolsuper = 't' then true else false end as superuser, 
    case when rolinherit = 't' then true else false end as caninherit, 
    case when rolcreaterole = 't' then true else false end as createrole, 
    case when rolcreatedb = 't' then true else false end as createdb, 
    case when rolcanlogin = 't' then true else false end as canlogin, 
    case when rolreplication = 't' then true else false end as replication, 
    case when rolbypassrls = 't' then true else false end as bypassrls, 
    case when rolconnlimit <= 0 then null else rolconnlimit end as connlimit 
from pg_catalog.pg_roles 
where rolname = %s