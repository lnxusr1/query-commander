SELECT
    waiting_session.sid AS wait_sid,
    waiting_session.username AS wait_user,
    holding_session.sid AS hold_sid,
    holding_session.username AS hold_user,
    waiting_sql.sql_text AS wait_statement,
    holding_sql.sql_text AS hold_statement
FROM
    sys.v$lock waiting_lock
JOIN
    sys.v$session waiting_session
    ON waiting_lock.sid = waiting_session.sid
JOIN
    sys.v$lock holding_lock
    ON waiting_lock.id1 = holding_lock.id1
    AND waiting_lock.id2 = holding_lock.id2
    AND holding_lock.block = 1
JOIN
    sys.v$session holding_session
    ON holding_lock.sid = holding_session.sid
LEFT JOIN
    sys.v$sql waiting_sql
    ON waiting_session.sql_id = waiting_sql.sql_id
LEFT JOIN
    sys.v$sql holding_sql
    ON holding_session.sql_id = holding_sql.sql_id
WHERE
    waiting_lock.block = 0
    AND waiting_lock.request > 0
ORDER BY
    wait_sid