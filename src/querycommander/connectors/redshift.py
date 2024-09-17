import sys
import os
import logging
import traceback

from datetime import datetime
from decimal import Decimal
import time

import pg8000
import pg8000.dbapi
from querycommander.connectors import Connector
#from querycommander.core.tokenizer import tokenizer
from querycommander.core.helpers import quote_ident


class Redshift(Connector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._type = "redshift"

        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port", 5432)
        self.options = kwargs.get("options", {})
        if "application_name" not in self.options:
            self.options["application_name"] = f"Query Commander [{str(self.tokenizer.username)[0:50]}]"

        self.user = kwargs.get("username")
        self.password = kwargs.get("password")
        self.database = kwargs.get("database")
        self.stats = {}

        self._notices = []
        self.columns = []

    def _save_notice(self, diag):
        self._notices.append(f"{diag.severity} - {diag.message_primary}")
    
    @property
    def explain_as_output(self):
        return True

    @property
    def exec_time(self):
        t = self.stats.get("end_time", self.stats.get("exec_time", 0)) - self.stats.get("start_time", 0)
        return t if t >= 0 else None
    
    @property
    def notices(self):
        if len(self.connection.notices) > 0:
            return "\n".join([str(x[b"M"].decode('UTF-8')) for x in self.connection.notices])
        else:
            return "Query executed successfully."
        
        return "\n".join([str(x) for x in self._notices])

    def open(self):
        if self.connection is None:
            try:
                self.connection = pg8000.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    #autocommit=True,
                    **self.options
                )

                #self.connection.add_notice_handler(self._save_notice)
                self.connection.autocommit = True

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

                if self.schema is not None and str(self.schema) != "":
                    #raise Exception(f"SET search_path TO {quote_ident(self.schema)};")
                    cur.execute(f"SET search_path TO {quote_ident(self.schema)};")

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
            except pg8000.dbapi.ProgrammingError as e:
                raise Exception(e.args[0]['M'])
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
                    headers = [{ "name": desc[0], "type": "text" } for desc in cur.description]
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

            #if str(query_type).lower() != "explain" and cur.rowcount <= 0:
            #    self.stats["end_time"] = time.time()
            #    return

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
        category = str(category).lower().strip()
        
        if category == "databases":
            return "select datname from pg_catalog.pg_database where not datistemplate and datname not in ('sys:internal','padb_harvest') order by datname"
        
        if category == "schemas":
            return "select nspname from pg_catalog.pg_namespace where nspname not in ('pg_auto_copy','catalog_history','pg_internal','pg_catalog', 'pg_toast', 'information_schema') order by nspname"
        
        if category == "schema":
            return "select 'CREATE SCHEMA ' || nspname || ';' as definition from pg_catalog.pg_namespace where nspname = %s"

        if category == "tables":
            return " ".join(
                [
                    "select tablename from (",
                    "select pg_tables.schemaname, pg_tables.tablename from pg_catalog.pg_tables",
                    "join pg_catalog.pg_namespace on pg_tables.schemaname = pg_namespace.nspname",
                    "join pg_catalog.pg_class on pg_tables.tablename = pg_class.relname and pg_namespace.oid = pg_class.relnamespace",
                    "where pg_class.relkind = 'r' and pg_class.oid not in (select inhrelid from pg_catalog.pg_inherits)",
                    ") x where tablename not like 'mv\\_tbl\\_\\_%%\\_\\_%%' and schemaname = %s order by tablename"
                ]
            )
        
        if category in ["table-detail", "partition-detail"]:
            return " ".join(
                [
                    "select schemaname, tablename, tableowner, tablespace from pg_catalog.pg_tables where schemaname = %s and tablename = %s"
                ]
            )

        if category in ["table", "partition"]:
            file_name = os.path.join(os.path.dirname(__file__), "extra_sql", "redshift_tables.sql")
            sql = None
            if os.path.exists(file_name):
                with open(file_name, "r", encoding="UTF-8") as fp:
                    sql = fp.read()

            return sql

        if category == "columns":
            return " ".join(
                [
                    "select a.attname as \"Column Name\",",
                    "a.attnum as \"#\", ",
                    "pg_catalog.format_type(a.atttypid, a.atttypmod) as \"Data Type\",",
                    "a.attnotnull as \"Not Null\",",
                    "pg_get_expr(d.adbin, d.adrelid) as \"Default\"",
                    "from pg_catalog.pg_attribute a",
                    "join pg_catalog.pg_class t on a.attrelid = t.oid",
                    "join pg_catalog.pg_namespace ns on t.relnamespace = ns.oid",
                    "left join pg_catalog.pg_attrdef d on (a.attrelid, a.attnum) = (d.adrelid, d.adnum)",
                    "where a.attnum > 0 and not a.attisdropped",
                    "and ns.nspname = %s",
                    "and t.relname = %s",
                    "order by attnum"
                ]
            )
        
        if category == "view-columns":
            return " ".join(
                [
                    "SELECT ",
                    "    a.attname AS column_name,",
                    "    a.atttypid::regtype AS data_type,",
                    "    a.attnum AS ordinal_position,",
                    "    a.attnotnull AS is_nullable",
                    "FROM ",
                    "    pg_attribute a",
                    "JOIN ",
                    "    pg_class c ON a.attrelid = c.oid",
                    "JOIN ",
                    "    pg_namespace n ON c.relnamespace = n.oid",
                    "WHERE ",
                    "    c.relkind = 'v'  ",
                    "    AND n.nspname = %s",
                    "    AND c.relname = %s",
                    "    AND a.attnum > 0 ",
                    "ORDER BY ",
                    "    a.attnum"
                ]
            )
        
        if category == "constraints":
            return " ".join(
                [
                    "select conname as \"Constraint Name\", pg_class.relname as \"Owner\", case pg_constraint.contype when 'f' then 'FOREIGN KEY' when 'c' then 'CHECK' when 'u' then 'UNIQUE' when 'p' then 'PRIMARY KEY' else '' end as \"Type\", pg_get_constraintdef(pg_constraint.oid) as \"Expression\" from pg_catalog.pg_constraint",
                    "join pg_catalog.pg_class on pg_constraint.conrelid = pg_class.oid",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where contype in ('f','p','u') and nspname = %s and pg_class.relname = %s order by conname"
                ]
            )
        
        #if category == "constraint":
        #    return " ".join(
        #        [
        #            "select CONCAT('ALTER TABLE ', pg_namespace.nspname, '.', pg_class.relname, ' ADD CONSTRAINT ', conname, ' ', pg_get_constraintdef(pg_constraint.oid), ';') as definition",
        #            "from pg_catalog.pg_constraint",
        #            "join pg_catalog.pg_namespace on pg_constraint.connamespace = pg_namespace.oid",
        #            "join pg_catalog.pg_class on pg_constraint.conrelid = pg_class.oid",
        #            "join pg_catalog.pg_namespace rns on pg_class.relnamespace = rns.oid",
        #            "where pg_namespace.nspname = %s and conname = %s;"
        #        ]
        #    )
        
        if category == "views":
            return " ".join([
                "select viewname ",
                "from pg_catalog.pg_views", 
                "    left join pg_catalog.stv_mv_info ",
                "        on pg_views.schemaname = stv_mv_info.schema and pg_views.viewname = stv_mv_info.name and coalesce(stv_mv_info.db_name,'-1') in (%s,'-1')",
                "where stv_mv_info.name is null and schemaname = %s order by viewname"
            ])
         
        if category == "view":
            return "select CONCAT(CONCAT(CONCAT(CONCAT(CONCAT('CREATE OR REPLACE VIEW ', schemaname), '.'), viewname), ' AS \n'), definition) as definition, schemaname, viewname, viewowner from pg_catalog.pg_views where schemaname = %s and viewname = %s;"
        
        if category == "mat_views":
            return "select name from pg_catalog.stv_mv_info where db_name = %s and schema = %s order by name"
        
        if category == "mat_view":
            return "select definition, schemaname, viewname, viewowner from pg_catalog.pg_views where schemaname = %s and viewname = %s;"
       
        if category == "functions":
            return " ".join(
                [
                    "select proname from pg_catalog.pg_proc ",
                    "join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid",
                    "where nspname = %s AND proname not like 'mv\\_sp\\_\\_%%\\_\\_%%' ",
                    "order by proname"
                ]
            )
        
        if category in ["function", "procedure"]:
            return " ".join(
                [
                    "select pg_catalog.pg_get_functiondef(pg_proc.oid) from pg_catalog.pg_proc ",
                    "join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid",
                    "where nspname = %s AND proname not like 'mv\\_sp\\_\\_%%\\_\\_%%' ",
                    "and proname = %s"
                ]
            )

        if category == "sessions":
            return "\n".join([
                "SELECT",
                "    pid,",
                "    usename AS user_name,",
                "    datname AS database_name,",
                "    client_addr AS client_address,",
                "    application_name,",
                "    state,",
                "    backend_start,",
                "    query_start,",
                "    query",
                "FROM",
                "    pg_stat_activity",
                "WHERE state = 'active'",
                "ORDER BY",
                "    pid"
            ]) 
       
        if category == "locks":
            return "\n".join([
                "SELECT",
                "    bl.pid AS wait_pid,",
                "    bl.usename AS wait_user,",
                "    wl.pid AS hold_pid,",
                "    wl.usename AS hold_user,",
                "    wl.text AS hold_statement,",
                "    bl.text AS wait_statement",
                "FROM",
                "    pg_catalog.stv_blocklist bl",
                "JOIN",
                "    stv_sessions wl",
                "    ON bl.locks = wl.process",
                "JOIN",
                "    stv_sessions ws",
                "    ON bl.pid = ws.pid",
                "ORDER BY",
                "    bl.pid"
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

            return meta, [self.database]

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

            return meta, [self.database]

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
            meta["menu_items"] = ["refresh", "copy", "ddl", "tab"]

            sql = self._sql("schemas")
            params = None

        if type == "schema":
            meta["type"] = "schema-folder"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Tables", "Views", "Materialized Views", "Procedures"]

        if type == "schema-folder" and target == "Tables":
            meta["type"] = "table"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("tables")
            params = [path.get("database")]

        if type == "schema-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("views")
            params = [self.database, path.get("database")]

        if type == "schema-folder" and target == "Materialized Views":
            meta["type"] = "mat_view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("mat_views")
            params = [self.database, path.get("database")]

        if type == "schema-folder" and target == "Procedures":
            meta["type"] = "procedure"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code-fork"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("functions")
            params = [path.get("database")]

        if type == "table":
            meta["type"] = "table-folder"
            meta["color"] = "orange"
            meta["classes"] = ["far", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Columns", "Constraints"]
        
        if type == "view":
            meta["type"] = "view-folder"
            meta["color"] = "orange"
            meta["classes"] = ["far", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Columns"]
        
        if type == "mat_view":
            meta["type"] = "mat_view-folder"
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

        if type == "view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("view-columns")
            params = [path.get("database"), path.get("view").rstrip()]

        if type == "mat_view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("view-columns")
            params = [path.get("database"), path.get("mat_view").rstrip()]

        if type == "table-folder" and target == "Constraints":
            meta["type"] = "constraint"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("constraints")
            params = [path.get("database"), path.get("table")]

        records = []

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                records.append(str(record[0]))

        return meta, records

    def ddl(self, type, target, path):
        sql = None
        params = None
        meta = { "type": None }

        if type == "schema":
            meta["type"] = "schema"

            sql = self._sql("schema")
            params = [target]

        if type == "table":
            meta["type"] = "table"

            sql = self._sql("table")
            params = [path.get("database"), target]

        if type == "view":
            meta["type"] = "view"

            sql = self._sql("view")
            params = [path.get("database"), path.get("view").rstrip()]

        if type == "mat_view":
            meta["type"] = "mat_view"

            sql = self._sql("mat_view")
            params = [path.get("database"), path.get("mat_view").rstrip()]

        if type == "procedure":
            meta["type"] = "procedure"

            sql = self._sql("procedure")
            params = [path.get("database"), path.get("procedure")]

        if type == "constraint":
            meta["type"] = "constraint"

            sql = self._sql("constraint")
            params = [path.get("database"), path.get("constraint")]

        statement = []

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                statement.append(str(record[0]))

        return meta, "\n".join(statement)

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
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("table-detail")
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[1],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[2],
                })

                data["meta"].append({
                    "name": "Schema",
                    "value": record[0],
                })

                data["meta"].append({
                    "name": "Tablespace",
                    "value": record[3],
                })

            sql = self._sql("columns")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self._sql("table")
            params = [path.get("database"), target]
            statement = []
            for headers, record in self.fetchmany(sql, params, 1000):
                statement.append(str(record[0]))

            data["sections"]["Source"]["data"] = "\n".join(statement)
    
        if type == "view":
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("view")
            params = [path.get("database"), target.rstrip()]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[2],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[3],
                })


                data["meta"].append({
                    "name": "Schema",
                    "value": record[1],
                })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("view-columns")
            params = [path.get("database"), target.rstrip()]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

        if type == "mat_view":
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("mat_view")
            params = [path.get("database"), target.rstrip()]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[2],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[3],
                })


                data["meta"].append({
                    "name": "Schema",
                    "value": record[1],
                })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("view-columns")
            params = [path.get("database"), target.rstrip()]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

        if type in ["function", "procedure"]:
            data = { 
                "meta": [], 
                "sections": {
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql(type)
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[2],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[3],
                })

                data["meta"].append({
                    "name": "Schema",
                    "value": record[1],
                })
                
                data["meta"].append({
                    "name": "Language",
                    "value": record[4],
                })

                data["meta"].append({
                    "name": "Arguments",
                    "value": record[5],
                })

                data["sections"]["Source"]["data"] = record[0]

        return data
        