SELECT
    p.ID AS process_id,
    p.USER AS user_name,
    p.HOST AS client_host,
    p.DB AS database_name,
    p.TIME AS time,
    p.STATE AS state,
    p.INFO AS query
FROM
    information_schema.processlist p
WHERE
    p.COMMAND = 'Query'
ORDER BY
    p.ID