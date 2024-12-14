SELECT
    bl.pid AS wait_pid,
    bl.usename AS wait_user,
    wl.pid AS hold_pid,
    wl.usename AS hold_user,
    wl.text AS hold_statement,
    bl.text AS wait_statement
FROM
    pg_catalog.stv_blocklist bl
JOIN
    stv_sessions wl
    ON bl.locks = wl.process
JOIN
    stv_sessions ws
    ON bl.pid = ws.pid
ORDER BY
    bl.pid