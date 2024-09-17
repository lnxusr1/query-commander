import json
import logging
from querycommander.core.config import settings as cfg
from querycommander.core.helpers import decrypt
#from querycommander.core.tokenizer import tokenizer


def get_db_connection(tokenizer, connection_name, database=None, schema=None):

    logger = logging.getLogger("DB_CONN")
    logger.setLevel(cfg.log_level)

    if database == "":
        database = None

    conn = cfg.sys_connections(connection_name)
    conn["schema"] = schema
    conn["tokenizer"] = tokenizer

    if conn is not None and tokenizer.validate_connection(conn):

        logger.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] - Connection selected: {connection_name} - {tokenizer.token}")
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
            from querycommander.connectors.postgres import Postgres

            # Security hole?
            conn["database"] = database if database is not None else conn["database"] if "database" in conn else None
            #if "database" not in conn:
            #    conn["database"] = database

            # Override
            #conn["database"] = database

            #logger.debug(f"Connection selected: {connection_name}")
            #logger.debug(f"Database selected: {database}")
            #logger.debug(f"Database selected: {conn.get('database')}")

            return Postgres(**conn)
        
        if conn.get("type") in ["mysql", "mariadb"]:
            from querycommander.connectors.mysqldb import MySQL
            conn["database"] = database if database is not None else conn["database"] if "database" in conn else None

            #if "database" not in conn:
            #    conn["database"] = database
            return MySQL(**conn)

        if conn.get("type") in ["oracle", "oracledb"]:
            conn["database"] = database if database is not None else conn["database"] if "database" in conn else None
            from querycommander.connectors.oracle import Oracle
            return Oracle(**conn)
        
        if conn.get("type") in ["redshift"]:
            from querycommander.connectors.redshift import Redshift
            return Redshift(**conn)
        
        if conn.get("type") in ["trino"]:
            from querycommander.connectors.trinodb import Trino
            conn["database"] = database if database is not None else conn["database"] if "database" in conn else None
            return Trino(**conn)

    return None
