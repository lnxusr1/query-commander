SELECT 
    pg_stat_activity_waiting.pid AS wait_pid,
    pg_stat_activity_waiting.usename AS wait_user,
    pg_stat_activity_holding.pid AS hold_pid,
    pg_stat_activity_holding.usename AS hold_user,
    pg_stat_activity_waiting.query AS wait_statement,
    pg_stat_activity_holding.query AS hold_statement
FROM 
    pg_stat_activity AS pg_stat_activity_waiting
JOIN 
    pg_locks AS waiting_locks 
    ON pg_stat_activity_waiting.pid = waiting_locks.pid
JOIN 
    pg_locks AS holding_locks 
    ON waiting_locks.locktype = holding_locks.locktype
    AND waiting_locks.database IS NOT DISTINCT FROM holding_locks.database
    AND waiting_locks.relation IS NOT DISTINCT FROM holding_locks.relation
    AND waiting_locks.page IS NOT DISTINCT FROM holding_locks.page
    AND waiting_locks.tuple IS NOT DISTINCT FROM holding_locks.tuple
    AND waiting_locks.virtualxid IS NOT DISTINCT FROM holding_locks.virtualxid
    AND waiting_locks.transactionid IS NOT DISTINCT FROM holding_locks.transactionid
    AND waiting_locks.classid IS NOT DISTINCT FROM holding_locks.classid
    AND waiting_locks.objid IS NOT DISTINCT FROM holding_locks.objid
    AND waiting_locks.objsubid IS NOT DISTINCT FROM holding_locks.objsubid
    AND waiting_locks.pid != holding_locks.pid
JOIN 
    pg_stat_activity AS pg_stat_activity_holding 
    ON holding_locks.pid = pg_stat_activity_holding.pid
WHERE 
    NOT waiting_locks.granted
ORDER BY 
    pg_stat_activity_waiting.pid