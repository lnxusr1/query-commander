SELECT
    s.sid,
    s.serial#,
    s.username AS user_name,
    s.osuser,
    s.program AS application_name,
    s.machine AS client_machine,
    s.terminal,
    s.status,
    s.schemaname AS schema_name,
    s.logon_time,
    s.module,
    s.action,
    s.client_info,
    s.event,
    s.wait_class,
    s.seconds_in_wait,
    s.state,
    s.sql_id,
    q.sql_text
FROM
    sys.v$session s
LEFT JOIN
    sys.v$sql q
    ON s.sql_id = q.sql_id
WHERE s.status = 'ACTIVE'
ORDER BY
    s.sid