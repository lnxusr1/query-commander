SELECT
    pid,
    usename AS user_name,
    datname AS database_name,
    client_addr AS client_address,
    application_name,
    state,
    backend_start,
    query_start,
    query
FROM
    pg_stat_activity
WHERE state = 'active'
ORDER BY
    pid