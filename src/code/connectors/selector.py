import json
import logging
from core.config import settings as cfg
from core.helpers import decrypt
from core.tokenizer import tokenizer


def get_db_connection(connection_name, database=None):
    if database == "":
        database = None

    conn = cfg.sys_connections(connection_name)
    if conn is not None and tokenizer.validate_connection(conn):

        logging.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] - Connection selected: {connection_name} - {tokenizer.token}")
        username = None
        password = None
        if str(cfg.sys_authenticator.get("type")) == "local":
            credentials = json.loads(decrypt(tokenizer.safe_password, tokenizer.credentials))
            if isinstance(credentials, dict):
                username = credentials.get("username")
                password = credentials.get("password")
            
            conn["username"] = username
            conn["password"] = password

        if conn.get("type") in ["postgres", "postgresql", "pgsql"]:
            from connectors.postgres import Postgres
            if "database" not in conn:
                conn["database"] = database
            return Postgres(**conn)
        
        if conn.get("type") in ["mysql", "mariadb"]:
            from connectors.mysqldb import MySQL
            if "database" not in conn:
                conn["database"] = database
            return MySQL(**conn)

        if conn.get("type") in ["oracle", "oracledb"]:
            from connectors.oracle import Oracle
            return Oracle(**conn)
        
        if conn.get("type") in ["redshift"]:
            from connectors.redshift import Redshift
            return Redshift(**conn)

    return None
