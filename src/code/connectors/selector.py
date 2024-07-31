import json
import copy
import logging
from core.config import settings as cfg
from core.helpers import decrypt
from core.tokenizer import tokenizer


def get_db_connection(connection_name, database=None):
    if database == "":
        database = None

    for conn_name in tokenizer.connections:
        if connection_name == conn_name:
            if conn_name in cfg.sys_connections:
                logging.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] - Connection selected: {conn_name} - {tokenizer.token}")
                if cfg.sys_connections.get(conn_name, {}).get("type") == "postgres":
                    username = None
                    password = None
                    if str(cfg.sys_authenticator.get("type")) == "local":
                        credentials = json.loads(decrypt(tokenizer.safe_password, tokenizer.credentials))
                        if isinstance(credentials, dict):
                            username = credentials.get("username")
                            password = credentials.get("password")
                        
                        cfg.sys_connections.get(conn_name)["username"] = username
                        cfg.sys_connections.get(conn_name)["password"] = password

                    elif str(cfg.sys_authenticator.get("type")) in ["ldap", "openldap"]:
                        #raise Exception("NOT IMPLEMENTED (connectors.selector - ldap/openldap)")
                        pass

                    from connectors.postgres import Postgres
                    conn = cfg.sys_connections.get(conn_name, {})
                    if "database" not in conn:
                        conn["database"] = database
                    return Postgres(**conn)

    return None
