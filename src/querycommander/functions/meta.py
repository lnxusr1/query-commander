import logging
from querycommander.connectors.selector import get_db_connection

logger = logging.getLogger()

#def get_info_dbs(tokenizer, connection_name):
#    logger.debug(f"================> {connection_name}")
#    connection = get_db_connection(connection_name)
#    if connection is None:
#        return None
#    
#    if not connection.open():
#        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] META: Unable to connect to server: {connection_name} - {tokenizer.token}")
#        return
#        
#    _, data = connection.meta("connection", connection_name, { "connection": connection_name })
#    return data


def get_info(tokenizer, request, response, data_type="meta"):
    resp = response

    connection_name = request.json_data.get("path", {}).get("connection")
    database = request.json_data.get("path", {}).get("database")
    connection = get_db_connection(tokenizer, connection_name, database=database)
    if connection is None:
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] META: Invalid database connection: {connection_name}/{database} - {tokenizer.token}")
        resp.output({ "ok": False, "error": "Invalid connection specified." })
        return

    if not connection.open():
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] META: Unable to connect to server: {connection_name}/{database} - {tokenizer.token}")
        resp.output({ "ok": False, "error": "Unable to connect to server." })
        return
    
    in_path = request.json_data.get("path", {})
    for item in in_path:
        if len(str(item)) > 255 or len(str(in_path.get("item"))) > 255:
            logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] META: Invalid meta data name (longer than 255 characters): {connection_name}/{database} - {tokenizer.token}")
            resp.output({ "ok": False, "error": "Invalid meta data request." })
            return

    if data_type == "meta":
        meta, data = connection.meta(str(request.json_data.get("type"))[0:100], str(request.json_data.get("target"))[0:255], in_path)

        tokenizer.update()
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Meta request complete {connection_name}/{database} - {tokenizer.token}")
        logger.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] {meta} - {tokenizer.token}")
        resp.output({ "ok": True, "meta": meta, "items": data })
        return

    if data_type == "ddl":
        meta, statement = connection.ddl(str(request.json_data.get("type"))[0:100], str(request.json_data.get("target"))[0:255], in_path)

        tokenizer.update()
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] DDL request complete {connection_name}/{database} - {tokenizer.token}")
        logger.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] {meta} - {tokenizer.token}")
        resp.output({ "ok": True, "meta": meta, "ddl": statement })
        return

    if data_type == "details":
        details = connection.details(str(request.json_data.get("type"))[0:100], str(request.json_data.get("target"))[0:255], in_path)
        detail_type = str(request.json_data.get("type"))[0:100]
        tokenizer.update()
        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Meta Detail request complete {connection_name}/{database} - {tokenizer.token}")
        logger.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] {detail_type} - {tokenizer.token}")
        resp.output({ "ok": True, "properties": details })
        return
