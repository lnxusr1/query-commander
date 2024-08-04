import sys
from core.config import settings as cfg
from core.interactions import Response
from core.tokenizer import tokenizer
from connectors.selector import get_db_connection


def get_query_results(connection_name, db_name, sql, query_type, start_record=0):
    resp = Response()

    connection = get_db_connection(connection_name, database=db_name)
    if connection is None:
        resp.output({ "ok": False, "error": "Invalid connection specified." })
        sys.exit()

    if not connection.open():
        resp.output({ "ok": False, "error": "Unable to connect to server.  Please check username/password." })
        sys.exit()

    data = { "error": "", "headers": [], "records": [], "output": "", "stats": {}, "has_more": False }
    try:
        if query_type == "explain":
            if connection._type == "oracle":
                sql = f"EXPLAIN PLAN FOR {sql}"
            else:
                sql = f"EXPLAIN {sql}"

        i = 0
        end_record = start_record + cfg.records_per_request
        for headers, record in connection.fetchmany(sql, params=None, size=201):
            data["headers"] = headers
            if i >= start_record and i < end_record:
                data["records"].append(record)

            i = i + 1
            
            if i > end_record:
                data["has_more"] = True
                break

        if len(data["headers"]) == 0:
            data["headers"] = connection.columns

        data["output"] = connection.notices
        data["stats"]["exec_time"] = connection.exec_time

        if query_type == "explain" and connection.explain_as_output:
            data["output"] = "\n".join(["\t".join(r) for r in data["records"]])
            data["records"] = []
            data["headers"] = []
            
    except Exception as e:
        data["error"] = str(e)

    resp.output({ 
        "ok": True, 
        "data": data
    })

    sys.exit()