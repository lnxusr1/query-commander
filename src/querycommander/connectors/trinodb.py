import os
import sys
import logging
import traceback

from datetime import datetime
from decimal import Decimal
import time

import trino
from querycommander.connectors import Connector
from querycommander.core.helpers import quote_ident

class Trino(Connector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._type = "trino"

        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port", 8080)
        self.options = kwargs.get("options", {})
        
        self.user = kwargs.get("username", "admin")
        self.password = kwargs.get("password")
        self.database = kwargs.get("catalog", kwargs.get("database"))
        self.databases = kwargs.get("databases")

        self.schema = kwargs.get("schema")
        self.stats = {}

        self._notices = []
        self.columns = []
    
    @property
    def explain_as_output(self):
        return True

    @property
    def exec_time(self):
        t = self.stats.get("end_time", self.stats.get("exec_time", 0)) - self.stats.get("start_time", 0)
        return t if t >= 0 else None
    
    @property
    def notices(self):
        if len(self._notices) == 0:
            return "Query executed successfully."
        
        return "\n".join([str(x) for x in self._notices])

    def open(self):
        if self.connection is None:
            try:
                if self.password is not None:
                    self.options["auth"] = trino.auth.BasicAuthentication(username=self.user, password=self.password)
                    self.options["http_scheme"] = "https"

                self.connection = trino.dbapi.connect(
                    host=self.host,
                    port=self.port,
                    catalog=self.database,
                    schema=self.schema,
                    user=self.user,
                    **self.options
                )

            except:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Unable to connect to database.")
                self.connection = None
                return False

        return True
    
    def commit(self):
        if self.connection is not None:
            try:
                self.connection.commit()
            except:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Unable to commit transaction.")
                return False
        
        return True

    def close(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Unable to close database connection.")
                return False

        return True
    
    def execute(self, sql, params=None):
        if self.connection is not None:
            try:
                self.logger.debug(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} -  SQL: {str(sql)} - {self.tokenizer.token}")
                if params is not None:
                    self.logger.debug(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - Params: {str(params)} - {self.tokenizer.token}")

                self.stats["start_time"] = time.time()
                cur = self.connection.cursor()

                sql = sql.rstrip(";")

                #cur.execute("SET AUTOCOMMIT TO ON")
                if params is None or len(params) == 0:
                    cur.execute(sql)
                else:
                    cur.execute(sql, params)
                self.stats["exec_time"] = time.time()

                # Move to last set in results (mimic psycopg2)
                #while cur.nextset():
                #    pass

                return cur
            except:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Query execution failed.")
                raise
            
        else:
            self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - Unable to establish connection - {self.tokenizer.token}")
            self.err.append("Unable to establish connection")
            raise ConnectionError("Unable to establish connection")

    def fetchmany(self, sql, params=None, size=None, query_type=None):
        if self.connection is not None:
            cur = self.execute(sql, params=params)
            
            if size is not None:
                cur.arraysize=size
            
            headers = []
            try:
                if cur.description is not None:
                    headers = [{ "name": desc.name, "type": "text" } for desc in cur.description]
            except TypeError:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(sql))
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Unable to parse columns.")
                headers = []
            except:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(sql))
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Unable to parse columns.")
                headers = []
                self.stats["end_time"] = time.time()
                raise

            self.columns = headers
            
            if len(headers) == 0:
                self.stats["end_time"] = time.time()
                return

            try:
                while True:
                    records = cur.fetchmany()
                    if not records:
                        break

                    for record in records:
                        record = list(record)
                        for i, item in enumerate(record):
                            if isinstance(item, datetime):
                                self.columns[i]["type"] = "date"
                            elif isinstance(item, bool):
                                self.columns[i]["type"] = "text"
                            elif isinstance(item, float) or isinstance(item, int) or isinstance(item, Decimal):
                                self.columns[i]["type"] = "number"
                            
                            record[i] = str(item) if item is not None else item
            
                        yield headers, record
            #except psycopg.ProgrammingError as e:
            #    if str(e) == "the last operation didn't produce a result":
            #        pass
            #    else:
            #        self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} -  {str(sys.exc_info()[0])} - {self.tokenizer.token}")
            #        self.logger.debug(str(traceback.format_exc()))
            #        self.stats["end_time"] = time.time()
            #        return
            except:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Unable to fetch rows for query.")
                self.stats["end_time"] = time.time()
                raise

            try:
                cur.close()
            except:
                self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                self.logger.debug(str(traceback.format_exc()))
                self.err.append("Unable to close cursor for query.")
                self.stats["end_time"] = time.time()
                raise

        else:
            self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - Unable to establish connection. - {self.tokenizer.token}")
            self.err.append("Unable to establish connection")
            self.stats["end_time"] = time.time()
            raise ConnectionError("Unable to establish connection")

        self.stats["end_time"] = time.time()

    def _sql(self, category):
        if category == "databases":
            return "show catalogs"
        
        if category == "schemas":
            return "select schema_name from information_schema.schemata order by schema_name"

        if category == "tables":
            return "select table_name from information_schema.tables where table_schema = ? order by table_name"
        
        if category == "table-detail":
            return "select table_catalog, table_schema, table_name, table_type from information_schema.tables where table_schema = ? and table_name = ? order by table_name"
        
        if category == "table-privs":
            return "select grantee as \"Role\", privilege_type as \"Privileges\", grantor as \"Granted By\", is_grantable as \"With Grant\" from information_schema.table_privileges where table_schema = ? and table_name = ? order by grantee, privilege_type"
        
        if category == "views":
            return "select table_name from information_schema.views where table_schema = ? order by table_name"

        if category == "view":
            return "select view_definition from information_schema.views where table_schema = ? order by table_name"

        if category == "columns":
            return "select column_name, ordinal_position, data_type, is_nullable, column_default from information_schema.columns where table_schema = ? and table_name = ? order by ordinal_position"
        
        if category == "sessions":
            return "select * from system.runtime.queries where state = 'RUNNING'"
        
        if category == "locks":
            return "SELECT * FROM system.runtime.queries WHERE state IN ('RUNNING', 'QUEUED') ORDER BY started DESC"
   
    def meta(self, type, target, path):
        sql = None
        params = None
        meta = { "type": None, "color": None, "class": None, "children": True, "menu_items": [] }

        if type == "database-list":
            meta["type"] = "database-list"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            sql = self._sql("databases")
            params = self.databases if isinstance(self.databases, list) and len(self.databases) > 0 else None

        if type == "schema-list":
            meta["type"] = "schema-list"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            sql = self._sql("schemas")
            params = None

        if type == "connection":
            meta["type"] = "database"
            meta["color"] = "brown"
            meta["classes"] = ["fa", "fa-database"]
            meta["menu_items"] = ["refresh", "copy", "tab"]

            sql = self._sql("databases")
            params = self.databases if isinstance(self.databases, list) and len(self.databases) > 0 else None

        if type == "database":
            meta["type"] = "db-folder"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Schemas"]
        
        if type == "db-folder" and target == "Schemas":
            meta["type"] = "schema"
            meta["color"] = "purple"
            meta["classes"] = ["fas", "fa-file-lines"]
            meta["menu_items"] = ["refresh", "copy", "tab"]

            sql = self._sql("schemas")
            params = None

        if type == "schema":
            meta["type"] = "schema-folder"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Tables", "Views"]
        
        if type == "schema-folder" and target == "Tables":
            meta["type"] = "table"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "details"]

            sql = self._sql("tables")
            params = [path.get("schema")]

        if type == "schema-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl"]

            sql = self._sql("views")
            params = [path.get("schema")]

        if type == "table":
            meta["type"] = "table-folder"
            meta["color"] = "orange"
            meta["classes"] = ["far", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Columns"]
        
        if type == "table-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("columns")
            params = [path.get("schema"), path.get("table")]

        records = []

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                records.append(str(record[0]))

        return meta, records

    def ddl(self, type, target, path):
        sql = None
        params = None
        meta = { "type": None }

        if type == "view":
            meta["type"] = "view"

            sql = self._sql("view")
            params = [path["schema"], path["view"]]

        statement = ""

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                statement = str(record[0])

        return meta, statement

    def details(self, type, target, path):
        sql = None
        params = None
        data = None

        if type in ["sessions", "locks"]:
            data = {
                "meta": [], 
                "sections": {
                    "Source": { "type": "code", "data": self._sql(type) }
                }
            }

        if type == "table":
            #tables: name, owner, object id, has row level security, partition by, tablespace
            #tables: columns, constraints, indexes, foreign keys, partitions, triggers, policies, permissions, DDL (code)
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    #"Constraints": { "type": "table", "headers": [], "records": [] },
                    #"Indexes": { "type": "table", "headers": [], "records": [] },
                    #"Partitions": { "type": "table", "headers": [], "records": [] },
                    #"Triggers": { "type": "table", "headers": [], "records": [] },
                    #"Policies": { "type": "table", "headers": [], "records": [] },
                    "Permissions": { "type": "table", "headers": [], "records": [] } #,
                    #"Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("table-detail")
            params = [path["schema"], target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[2],
                })

                data["meta"].append({
                    "name": "Type",
                    "value": record[3],
                })

                data["meta"].append({
                    "name": "Catalog",
                    "value": record[0],
                })


                data["meta"].append({
                    "name": "Schema",
                    "value": record[1],
                })

            sql = self._sql("columns")
            params = [path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            #sql = self._sql("constraints")
            #params = [path["schema"], target]
            #for headers, record in self.fetchmany(sql, params, 1000):
            #    data["sections"]["Constraints"]["headers"] = headers
            #    data["sections"]["Constraints"]["records"].append(record)

            #sql = self._sql("indexes")
            #params = [path["schema"], target]
            #for headers, record in self.fetchmany(sql, params, 1000):
            #    data["sections"]["Indexes"]["headers"] = headers
            #    data["sections"]["Indexes"]["records"].append(record)

            sql = self._sql("table-privs")
            params = [path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        return data
