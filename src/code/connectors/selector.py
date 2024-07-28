#!/usr/bin/env python

import sys
import json
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
                    if str(cfg.sys_authenticator.get("type")) == "config":
                        credentials = cfg.sys_connections.get(conn_name, {}).get("credentials", [])[0]
                        if isinstance(credentials, dict):
                            
                            #TODO: Enable storing these in SecretsManager

                            username = credentials.get("username")
                            password = credentials.get("password")

                    elif str(cfg.sys_authenticator.get("type")) == "local":
                        credentials = json.loads(decrypt(tokenizer.safe_password, tokenizer.credentials))
                        if isinstance(credentials, dict):
                            username = credentials.get("username")
                            password = credentials.get("password")

                    elif str(cfg.sys_authenticator.get("type")) in ["ldap", "openldap"]:
                        raise Exception("NOT IMPLEMENTED (connectors.selector - ldap/openldap)")

                    if username is not None and password is not None:
                        from connectors.postgres import Postgres
                        return Postgres(**cfg.sys_connections.get(conn_name, {}), database=database, username=username, password=password)

    return None

if __name__ == "__main__":
    print("Location: /\n")
    sys.exit()