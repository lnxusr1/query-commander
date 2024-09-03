import sys
import traceback
import logging
from querycommander.core.config import settings as cfg
from querycommander.core.helpers import get_utc_now
from querycommander.connectors.selector import get_db_connection

logger = logging.getLogger()

def get_query_results(tokenizer, response, connection_name, db_name, sql, query_type, schema_name=None, start_record=0):

    resp = response
    records_per_request = cfg.records_per_request

    #limit_exceeded = False
    if cfg.rate_limit_records > 0 and cfg.rate_limit_period > 0:
        remaining_records = tokenizer.get_records_remaining()
        if records_per_request > remaining_records:
            records_per_request = remaining_records

    connection = get_db_connection(tokenizer, connection_name, database=db_name, schema=schema_name)
    if connection is None:
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] QUERY: Invalid database connection: {connection_name}/{db_name} - {tokenizer.token}")
        resp.output({ "ok": False, "error": "Invalid connection specified." })
        return

    if not connection.open():
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] QUERY: Unable to connect to server: {connection_name}/{db_name} - {tokenizer.token}")
        resp.output({ "ok": False, "error": "Unable to connect to server." })
        return

    data = { "error": "", "headers": [], "records": [], "output": "", "stats": {}, "has_more": False }
    try:
        if query_type == "explain":
            if connection._type == "oracle":
                sql = f"EXPLAIN PLAN FOR {sql}"
            else:
                sql = f"EXPLAIN {sql}"

        i = 0
        end_record = start_record + records_per_request
        if records_per_request > 0:
            for headers, record in connection.fetchmany(sql, params=None, size=201, query_type=query_type):
                data["headers"] = headers
                if i >= start_record and i < end_record:
                    data["records"].append(record)

                i = i + 1
                
                if i > end_record:
                    data["has_more"] = True
                    break
        else:
            data["error"] = "Record rate limit exceeded."

        if len(data["headers"]) == 0:
            data["headers"] = connection.columns

        data["output"] = connection.notices
        data["stats"]["exec_time"] = connection.exec_time

        if query_type == "explain" and connection.explain_as_output:
            data["output"] = "\n".join(["\t".join(r) for r in data["records"]])
            data["records"] = []
            data["headers"] = []
        
        connection.commit()
        connection.close()
    except Exception as e:
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Failed to retrieve results: {connection_name}/{db_name} - {tokenizer.token}")
        logger.debug(str(sys.exc_info()[0]))
        logger.debug(str(traceback.format_exc()))
        data["error"] = str(e)

    if cfg.rate_limit_records > 0 and cfg.rate_limit_period > 0:
        if len(data["records"]) > 0:
            history_data = tokenizer.history()
            history_data.append([get_utc_now().strftime("%Y-%m-%d %H:%M:%S"), len(data["records"])])
            tokenizer.set("history", history_data)

    logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Query results retrieved: {connection_name}/{db_name} - {tokenizer.token}")

    resp.output({ 
        "ok": True, 
        "data": data
    })

    return