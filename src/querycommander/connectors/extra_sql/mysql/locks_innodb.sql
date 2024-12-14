SELECT
    rtrx.trx_id AS wait_trx_id,
    rtrx.trx_mysql_thread_id AS wait_pid,
    rtrx.trx_query AS wait_statement,
    rtrx.trx_mysql_thread_id AS wait_user,
    btrx.trx_id AS hold_trx_id,
    btrx.trx_mysql_thread_id AS hold_pid,
    btrx.trx_query AS hold_statement,
    btrx.trx_mysql_thread_id AS hold_user
FROM
    information_schema.innodb_lock_waits w
JOIN
    information_schema.innodb_trx rtrx
    ON rtrx.trx_id = w.requesting_trx_id
JOIN
    information_schema.innodb_trx btrx
    ON btrx.trx_id = w.blocking_trx_id
ORDER BY
    rtrx.trx_mysql_thread_id