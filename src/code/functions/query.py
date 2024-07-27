#!/usr/bin/env python

import sys
import logging
from core.interactions import Response
from core.tokenizer import tokenizer
from connectors.selector import get_db_connection


def get_query_results(connection_name, sql, query_type):

    resp = Response()

    connection = get_db_connection(connection_name, database=None)
    if connection is None:
        resp.output({ "ok": False, "error": "Invalid connection specified." })
        sys.exit()

    if not connection.open():
        resp.output({ "ok": False, "error": "Unable to connect to server.  Please check username/password." })
        sys.exit()

    data = { "error": "", "headers": [], "records": [], "output": "" }
    try:
        if query_type == "explain":
            sql = f"EXPLAIN {sql}"

        for headers, record in connection.fetchmany(sql, params=None, size=1000):
            data["headers"] = headers
            data["records"].append(record)

        data["output"] = connection.notices

        if query_type == "explain":
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