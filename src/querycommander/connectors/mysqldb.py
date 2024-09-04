import sys
import logging
import traceback

from datetime import datetime
from decimal import Decimal
import time

import mysql.connector
from mysql.connector import errorcode
from querycommander.connectors import Connector
#from querycommander.core.tokenizer import tokenizer


class MySQL(Connector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._type = "mysql"
        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port", 5432)
        self.options = kwargs.get("options", {})
        
        self.user = kwargs.get("username")
        self.password = kwargs.get("password")
        self.database = kwargs.get("database")
        self.databases = kwargs.get("databases")
        self.stats = {}

        self._notices = []
        self.columns = []
    
    @property
    def notices(self):
        return "Query executed successfully."

    @property
    def exec_time(self):
        t = self.stats.get("end_time", self.stats.get("exec_time", 0)) - self.stats.get("start_time", 0)
        return t if t >= 0 else None

    def open(self):
        if self.connection is None:
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    autocommit=True,
                    **self.options
                )

            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                    self.logger.debug(str(traceback.format_exc()))
                    self.err.append("Invalid username or password.")
                    self.connection = None
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                    self.logger.debug(str(traceback.format_exc()))
                    self.err.append("Selected database does not exist.")
                    self.connection = None
                else:
                    self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                    self.logger.debug(str(traceback.format_exc()))
                    self.err.append("Unable to connect to database.")
                    self.connection = None

                return False
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
                cur.execute(sql, params=params)
                self.stats["exec_time"] = time.time()

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

            if size is None:
                size = 1000

            headers = []
            try:
                if cur.description is not None:
                    headers = [{ "name": desc[0], "type": "text" } for desc in cur.description]
            except StopIteration:
                pass
            except GeneratorExit:
                pass
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
            
#            if cur.rowcount <= 0:
#                self.stats["end_time"] = time.time()
#                return

            try:
                while True:
                    records = cur.fetchmany(size=size)
                    #if records is not None:
                    #    self.logger.debug(len(records))
                    if not records or len(records) == 0:
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
        category = str(category).lower().strip()

        if category == "databases":
            return "show databases"
        
        if category == "tables":
            return "select table_name from information_schema.tables where table_type != 'VIEW' and table_schema = %s order by table_name"
    
        if category == "views":
            return "select table_name from information_schema.tables where table_type = 'VIEW' and table_schema = %s order by table_name"

        if category in ["table-info", "view-info"]:
            return "select table_schema, table_name, table_collation, engine, table_type from information_schema.tables where table_schema = %s and table_name = %s"

        if category in ["table", "view"]:
            return "show create table `{OBJECT_NAME}`"

        if category == "functions":
            return "select specific_name from information_schema.routines where routine_type = 'FUNCTION' and routine_schema = %s order by specific_name"
        
        if category == "function":
            return "show create function `{OBJECT_NAME}`"

        if category == "procedures":
            return "select specific_name from information_schema.routines where routine_type = 'PROCEDURE' and routine_schema = %s order by specific_name"

        if category == "procedure":
            return "show create procedure `{OBJECT_NAME}`"
        
        if category == "trigger":
            return "show create trigger `{OBJECT_NAME}`"

        if category == "columns":
            return "select column_name from information_schema.columns where table_schema = %s and table_name = %s order by ordinal_position"
        
        if category == "constraints":
            return " ".join(
                [
                    "select * from (",
                    "select distinct constraint_name, constraint_schema, table_name from information_schema.referential_constraints",
                    "union all",
                    "select constraint_name, table_schema as constraint_schema, table_name from information_schema.table_constraints where constraint_type != 'CHECK' ",
                    ") constraints where constraint_schema = %s and table_name = %s"
                    "order by constraint_name"
                ]
            )
        
        if category == "indexes":
            return " ".join(
                [
                    "SELECT distinct index_name, table_schema, table_name",
                    "FROM INFORMATION_SCHEMA.STATISTICS",
                    "WHERE TABLE_SCHEMA = %s and table_name = %s order by index_name"
                ]
            )

        if category == "triggers":
            return "select trigger_name from information_schema.triggers where event_object_schema = %s and event_object_table = %s order by trigger_name"

        if category == "schema-grants":
            return "select grantee as \"Role\", privilege_type as \"Privilege\", is_grantable as \"With Grant\" from information_schema.schema_privileges where table_schema = %s order by grantee, privilege_type"

        if category == "grants":
            return " ".join(
                [
                    "select grantee as \"Role\", privilege_type as \"Privilege\", is_grantable as \"With Grant\"",
                    "from information_schema.table_privileges where table_schema = %s and table_name in ('global_priv',%s)",
                    "order by grantee, privilege_type, is_grantable"
                ]
            )

        if category == "global-grants":
            return "select grantee as \"Role\", privilege_type as \"Privilege\", is_grantable as \"With Grant\" from information_schema.user_privileges order by grantee, privilege_type, is_grantable"

        if category == "sessions":
            return "\n".join([
                "SELECT",
                "    p.ID AS process_id,",
                "    p.USER AS user_name,",
                "    p.HOST AS client_host,",
                "    p.DB AS database_name,",
                "    p.TIME AS time,",
                "    p.STATE AS state,",
                "    p.INFO AS query",
                "FROM",
                "    information_schema.processlist p",
                "WHERE",
                "    p.COMMAND = 'Query'",
                "ORDER BY",
                "    p.ID"
            ])
        
        if category == "locks":
            return "\n".join([
                "SELECT",
                "    rtrx.trx_id AS wait_trx_id,",
                "    rtrx.trx_mysql_thread_id AS wait_pid,",
                "    rtrx.trx_query AS wait_statement,",
                "    rtrx.trx_mysql_thread_id AS wait_user,",
                "    btrx.trx_id AS hold_trx_id,",
                "    btrx.trx_mysql_thread_id AS hold_pid,",
                "    btrx.trx_query AS hold_statement,",
                "    btrx.trx_mysql_thread_id AS hold_user",
                "FROM",
                "    information_schema.innodb_lock_waits w",
                "JOIN",
                "    information_schema.innodb_trx rtrx",
                "    ON rtrx.trx_id = w.requesting_trx_id",
                "JOIN",
                "    information_schema.innodb_trx btrx",
                "    ON btrx.trx_id = w.blocking_trx_id",
                "ORDER BY",
                "    rtrx.trx_mysql_thread_id"
            ])

        return None
    
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
            params = None

        if type == "schema-list":
            meta["type"] = "schema-list"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            # MySQL only uses Schemas (like Oracle)
            return meta, None

        if type == "connection":
            meta["type"] = "database"
            meta["color"] = "brown"
            meta["classes"] = ["fa", "fa-database"]
            meta["menu_items"] = ["refresh", "tab", "copy", "ddl", "details"]

            sql = self._sql("databases")
            params = None

        if type == "database":
            meta["type"] = "db-folder"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Tables", "Views", "Functions", "Procedures"]

        if type == "db-folder" and target == "Tables":
            meta["type"] = "table"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("tables")
            params = [path.get("database")]

        if type == "db-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("views")
            params = [path.get("database")]

        if type == "db-folder" and target == "Functions":
            meta["type"] = "function"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("functions")
            params = [path.get("database")]

        if type == "db-folder" and target == "Procedures":
            meta["type"] = "procedure"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code-fork"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("procedures")
            params = [path.get("database")]

        if type == "table":
            meta["type"] = "table-folder"
            meta["color"] = "orange"
            meta["classes"] = ["far", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Columns", "Constraints", "Indexes", "Triggers"]
        
        if type == "view":
            meta["type"] = "view-folder"
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
            params = [path.get("database"), path.get("table")]

        if type == "table-folder" and target == "Constraints":
            meta["type"] = "constraint"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("constraints")
            params = [path.get("database"), path.get("table")]

        if type == "table-folder" and target == "Indexes":
            meta["type"] = "index"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("indexes")
            params = [path.get("database"), path.get("table")]

        if type == "table-folder" and target == "Triggers":
            meta["type"] = "trigger"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("triggers")
            params = [path.get("database"), path.get("table")]

        if type == "view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("columns")
            params = [path.get("database"), path.get("view")]

        records = []

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                if meta["type"] in ["database-list", "database"] and isinstance(self.databases, list) and len(self.databases) > 0:
                    if str(record[0]) not in self.databases:
                        continue

                records.append(str(record[0]))

        return meta, records
    
    def ddl(self, type, target, path):
        sql = None
        params = None
        meta = { "type": None }
        statement = ""
        code_column = 0

        if type == "database":
            meta["type"] = "database"

            sql = self._sql("databases")
            params = None

            for _, record in self.fetchmany(sql, params, 1000):
                if record[0] == target:
                    statement = f"CREATE DATABASE `{record[0]}`;"

                    return meta, statement
            
            return meta, ""

        if type == "table":
            meta["type"] = "table"
            code_column = 1

            sql = self._sql("table").format(OBJECT_NAME=target)
            params = None

        if type == "view":
            meta["type"] = "view"
            code_column = 1

            sql = self._sql("view").format(OBJECT_NAME=target)
            params = None

        if type in ["index", "constraint"]:
            meta["type"] = type
            code_column = 1

            sql = self._sql("table").format(OBJECT_NAME=path.get("table"))
            params = None

        if type == "function":
            meta["type"] = "function"
            code_column = 2

            sql = self._sql("function").format(OBJECT_NAME=target)
            params = None

        if type == "procedure":
            meta["type"] = "procedure"
            code_column = 2

            sql = self._sql("procedure").format(OBJECT_NAME=target)
            params = None

        if type == "trigger":
            meta["type"] = "trigger"
            code_column = 2

            sql = self._sql("trigger").format(OBJECT_NAME=target)
            params = None

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                statement = str(record[code_column])

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

        if type == "database":
            data = { 
                "meta": [], 
                "sections": {
                    "Global Permissions": { "type": "table", "headers": [], "records": [] },
                    "Schema Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("databases")
            params = None

            schema_name = None
            for _, record in self.fetchmany(sql, params, 1000):
                if record[0] == target:
                    schema_name = record[0]
                    data["meta"].append({
                        "name": "Name",
                        "value": schema_name,
                    })

                    data["sections"]["Source"]["data"] = f"CREATE DATABASE `{schema_name}`;"

            if schema_name is not None:
                sql = self._sql("schema-grants")
                params = [schema_name]
                for headers, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Schema Permissions"]["headers"] = headers
                    data["sections"]["Schema Permissions"]["records"].append(record)

                sql = self._sql("global-grants")
                params = None
                for headers, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Global Permissions"]["headers"] = headers
                    data["sections"]["Global Permissions"]["records"].append(record)

        if type == "table":
            data = { 
                "meta": [], 
                "sections": {
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("table-info")
            params = [path.get("database"), target]
            # table_schema, table_name, table_collation, engine, table_type

            table_name = None
            for _, record in self.fetchmany(sql, params, 1000):
                table_name = record[1]
                data["meta"].append({
                    "name": "Name",
                    "value": table_name,
                })

                data["meta"].append({
                    "name": "Type",
                    "value": record[4],
                })

                data["meta"].append({
                    "name": "Schema",
                    "value": record[0],
                })

                data["meta"].append({
                    "name": "Engine",
                    "value": record[3],
                })

                data["meta"].append({
                    "name": "Collation",
                    "value": record[2],
                })

            if table_name is not None:
                sql = self._sql("table").format(OBJECT_NAME=table_name)
                params = None
                for _, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Source"]["data"] = record[1]

            sql = self._sql("grants")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type == "view":
            data = { 
                "meta": [], 
                "sections": {
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("view-info")
            params = [path.get("database"), target]
            # table_schema, table_name, table_collation, engine, table_type

            table_name = None
            for _, record in self.fetchmany(sql, params, 1000):
                table_name = record[1]
                data["meta"].append({
                    "name": "Name",
                    "value": table_name,
                })

                data["meta"].append({
                    "name": "Type",
                    "value": record[4],
                })

                data["meta"].append({
                    "name": "Schema",
                    "value": record[0],
                })

            if table_name is not None:
                sql = self._sql("view").format(OBJECT_NAME=table_name)
                params = None
                for _, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Source"]["data"] = record[1]

            sql = self._sql("grants")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)
    
        return data