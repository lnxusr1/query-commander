import sys
from core.interactions import Response
from core.tokenizer import tokenizer
from connectors.selector import get_db_connection


def get_info(request, data_type="meta"):

    resp = Response()
    
    connection = get_db_connection(request.json_data.get("path", {}).get("connection"), database=request.json_data.get("path", {}).get("database"))
    if connection is None:
        resp.output({ "ok": False, "error": "Invalid connection specified." })
        sys.exit()

    if not connection.open():
        resp.output({ "ok": False, "error": "Unable to connect to server.  Please check username/password." })
        sys.exit()
    
    in_path = request.json_data.get("path", {})
    for item in in_path:
        if len(str(item)) > 255 or len(str(in_path.get("item"))) > 255:
            return
        
    if data_type == "meta":
        meta, data = connection.meta(str(request.json_data.get("type"))[0:100], str(request.json_data.get("target"))[0:255], in_path)

        tokenizer.update()
        resp.output({ "ok": True, "meta": meta, "items": data })
        sys.exit()

    if data_type == "ddl":
        meta, statement = connection.ddl(str(request.json_data.get("type"))[0:100], str(request.json_data.get("target"))[0:255], in_path)

        tokenizer.update()
        resp.output({ "ok": True, "meta": meta, "ddl": statement })
        sys.exit()

    if data_type == "details":
        details = connection.details(str(request.json_data.get("type"))[0:100], str(request.json_data.get("target"))[0:255], in_path)

        tokenizer.update()
        resp.output({ "ok": True, "properties": details })
        sys.exit()
