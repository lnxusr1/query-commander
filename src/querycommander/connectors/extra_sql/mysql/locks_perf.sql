SELECT
    req_trx.THREAD_ID AS wait_trx_id,
    req_thr.PROCESSLIST_ID AS wait_pid,
    req_thr.PROCESSLIST_INFO AS wait_statement,
    req_thr.PROCESSLIST_USER AS wait_user,
    blk_trx.THREAD_ID AS hold_trx_id,
    blk_thr.PROCESSLIST_ID AS hold_pid,
    blk_thr.PROCESSLIST_INFO AS hold_statement,
    blk_thr.PROCESSLIST_USER AS hold_user
FROM
    performance_schema.data_lock_waits AS dlw
JOIN
    performance_schema.data_locks AS req_trx
    ON dlw.REQUESTING_ENGINE_LOCK_ID = req_trx.ENGINE_LOCK_ID
JOIN
    performance_schema.threads AS req_thr
    ON req_trx.THREAD_ID = req_thr.THREAD_ID
JOIN
    performance_schema.data_locks AS blk_trx
    ON dlw.BLOCKING_ENGINE_LOCK_ID = blk_trx.ENGINE_LOCK_ID
JOIN
    performance_schema.threads AS blk_thr
    ON blk_trx.THREAD_ID = blk_thr.THREAD_ID
ORDER BY
    req_thr.PROCESSLIST_ID