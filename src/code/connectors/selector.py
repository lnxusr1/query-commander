import json
import copy
import logging
from core.config import settings as cfg
from core.helpers import decrypt
from core.tokenizer import tokenizer


def get_db_connection(connection_name, database=None):
    if database == "":
        database = None

    for cn in tokenizer.connections:
        conn_name = cn["name"]
        if connection_name == conn_name:
            if conn_name in cfg.sys_connections:
                logging.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] - Connection selected: {conn_name} - {tokenizer.token}")
                username = None
                password = None
                if str(cfg.sys_authenticator.get("type")) == "local":
                    credentials = json.loads(decrypt(tokenizer.safe_password, tokenizer.credentials))
                    if isinstance(credentials, dict):
                        username = credentials.get("username")
                        password = credentials.get("password")
                    
                    cfg.sys_connections.get(conn_name)["username"] = username
                    cfg.sys_connections.get(conn_name)["password"] = password

                if cfg.sys_connections.get(conn_name, {}).get("type") in ["postgres", "postgresql", "pgsql"]:
                    from connectors.postgres import Postgres
                    conn = cfg.sys_connections.get(conn_name, {})
                    if "database" not in conn:
                        conn["database"] = database
                    return Postgres(**conn)
                
                if cfg.sys_connections.get(conn_name, {}).get("type") in ["mysql", "mariadb"]:
                    from connectors.mysqldb import MySQL
                    conn = cfg.sys_connections.get(conn_name, {})
                    if "database" not in conn:
                        conn["database"] = database
                    return MySQL(**conn)

    return None
