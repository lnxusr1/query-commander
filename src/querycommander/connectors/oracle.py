import sys
import re
import logging
import traceback

from datetime import datetime
from decimal import Decimal
import time

import oracledb
import oracledb.exceptions
from querycommander.connectors import Connector
#from querycommander.core.tokenizer import tokenizer


def quote_ident_oracle(identifier):
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', identifier):
        raise ValueError("Invalid identifier")
    return f'"{identifier.upper()}"'

def is_plsql_block(query):
    query = query.strip().lower()

    if query.startswith('begin') and 'end' in query:
        return True

    if 'declare' in query or 'exception' in query:
        return True

    return False

def preprocess_query(sql):
    sql = sql.strip()
    if is_plsql_block(sql):
        if not sql.endswith(';'):
            sql += ';'
    else:
        if sql.endswith(';'):
            sql = sql.rstrip(';')
    
    return sql

oracledb.defaults.fetch_lobs = False 

class Oracle(Connector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._type = "oracle"

        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port", 5432)
        self.options = kwargs.get("options", {})
        
        self.user = kwargs.get("username")
        self.password = kwargs.get("password")
        self.service_name = kwargs.get("service_name")
        self.schemas = kwargs.get("schemas", kwargs.get("databases"))
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
                self.connection = oracledb.connect(
                    host=self.host,
                    port=self.port,
                    service_name=self.service_name,
                    user=self.user,
                    password=self.password,
                    **self.options
                )

                cursor = self.connection.cursor()
                cursor.callproc("DBMS_APPLICATION_INFO.SET_MODULE", (f"Query Commander [{self.tokenizer.username}]", "Initialization"))
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

                if self.schema is not None:
                    cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {quote_ident_oracle(self.database)}")

                #if sql.rstrip().endswith(";"):
                #    sql = sql.rstrip().rstrip(";")
                cur.callproc("dbms_output.enable")
                sql = preprocess_query(sql)
                cur.execute(sql, parameters=params)

                if sql.startswith("EXPLAIN PLAN FOR "):
                    cur.execute("SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', null, 'ALL'))")

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
            
            if size is not None:
                cur.arraysize=size
            
            headers = []
            try:
                if cur.description is not None:
                    headers = [{ "name": desc[0], "type": "text" } for desc in cur.description]
            except TypeError:
                #self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                #self.logger.debug(str(sql))
                #self.logger.debug(str(traceback.format_exc()))
                #self.err.append("Unable to parse columns.")
                headers = []
            except StopIteration:
                pass
            except GeneratorExit:
                pass
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
            except oracledb.InterfaceError as e:
                error_obj, = e.args
                if error_obj.full_code == "DPY-1003":
                    # tune this size for your application
                    chunk_size = 100

                    # create variables to hold the output
                    lines_var = cur.arrayvar(str, chunk_size)
                    num_lines_var = cur.var(int)
                    num_lines_var.setvalue(0, chunk_size)

                    # fetch the text that was added by PL/SQL
                    while True:
                        cur.callproc("dbms_output.get_lines", (lines_var, num_lines_var))
                        num_lines = num_lines_var.getvalue()
                        lines = lines_var.getvalue()[:num_lines]
                        for line in lines:
                            self._notices.append(str(line))
                        if num_lines < chunk_size:
                            break

                else:
                    self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(sys.exc_info()[0])} - {self.tokenizer.token}")
                    self.logger.debug(str(traceback.format_exc()))
                    self.err.append("Unable to fetch rows for query.")
                    self.stats["end_time"] = time.time()
                    raise

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

        if category == "ddl":
            return "SELECT DBMS_METADATA.GET_DDL(:1, :2, :3) FROM DUAL"
        
        if category == "schemas":
            if isinstance(self.schemas, list) and len(self.schemas) > 0:
                in_str = []
                for i in range(0,len(self.schemas)):
                    in_str.append(":"+str(i+1))

                return f"select distinct table_schema from sys.all_tab_privs where table_schema NOT IN ('SYS', 'SYSTEM', 'MDSYS', 'ORDSYS', 'OLAPSYS', 'APEXSYS') and table_schema in ({', '.join(in_str)}) order by table_schema"
            else:
                return "select distinct table_schema from sys.all_tab_privs where table_schema NOT IN ('SYS', 'SYSTEM', 'MDSYS', 'ORDSYS', 'OLAPSYS', 'APEXSYS') order by table_schema"
        
        if category == "tables":
            return "select table_name from sys.all_tables where owner = :1 and table_name not in (select mview_name from sys.all_mviews where owner = :2) order by table_name"
        
        if category == "table":
            return "select owner, table_name, tablespace_name from sys.all_tables where owner = :1 and table_name = :2"
        
        if category == "views":
            return "select view_name from sys.all_views where owner = :1 order by view_name"

        if category == "view":
            return "select owner, view_name, read_only from sys.all_views where owner = :1 and view_name = :2 order by view_name"

        if category == "mat_views":
            return "select mview_name from sys.all_mviews where owner = :1 order by mview_name"
        
        if category == "mat_view":
            return "select owner, mview_name, updatable, refresh_mode, refresh_method, build_mode, last_refresh_date from sys.all_mviews where owner = :1 and mview_name = :2 order by mview_name"
        
        if category == "sequences":
            return "select sequence_name from sys.all_sequences where sequence_owner = :1 order by sequence_name"

        if category == "sequence":
            return "select sequence_owner, sequence_name, min_value, max_value, increment_by, cache_size, last_number from sys.all_sequences where sequence_owner = :1 and sequence_name = :2 order by sequence_name"

        if category in ["functions","packages","procedures"]:
            return "select object_name from sys.all_procedures where owner != 'SYS' and procedure_name is null and object_type = :1 and owner = :2 order by object_name"

        if category in ["function","package","procedure"]:
            return "select owner, object_name from sys.all_procedures where owner != 'SYS' and procedure_name is null and object_type = :1 and owner = :2 and object_name = :3 order by object_name"

        if category == "columns":
            return "select column_name as \"Column Name\", column_id as \"#\", data_type as \"Data Type\", data_length as \"Length\", data_precision as \"Precision\", data_scale as \"Scale\", nullable as \"Nullable\", data_default as \"Default\" from sys.all_tab_columns where owner = :1 and table_name = :2 order by column_id"

        if category == "constraints":
            return "select constraint_name from sys.all_constraints where constraint_type in ('R','P','U') and owner = :1 and table_name = :2 order by constraint_name"

        if category == "indexes":
            return "select index_name from sys.all_indexes where index_type != 'IOT - TOP' and table_owner = :1 and table_name = :2 order by index_name"

        if category == "triggers":
            return "select trigger_name from sys.all_triggers where table_owner = :1 and table_name = :2 order by trigger_name"

        if category == "grants":
            return "select grantee as \"Role\", privilege as \"Privilege\", grantor as \"Granted By\", grantable as \"With Grant\" from sys.all_tab_privs where type = :1 and table_schema = :2 and table_name = :3 order by grantee, privilege"

        if category == "partitions":
            return "select PARTITION_NAME from sys.all_tab_partitions where table_owner = :1 and table_name = :2 order by PARTITION_POSITION"

        if category == "subpartitions":
            return "select subpartition_name from sys.all_tab_subpartitions where table_owner = :1 and table_name = :2 and partition_name = :3 order by SUBPARTITION_POSITION"
        
        if category == "sessions":
            return "\n".join(
                [
                    "SELECT",
                    "    s.sid,",
                    "    s.serial#,",
                    "    s.username AS user_name,",
                    "    s.osuser,",
                    "    s.program AS application_name,",
                    "    s.machine AS client_machine,",
                    "    s.terminal,",
                    "    s.status,",
                    "    s.schemaname AS schema_name,",
                    "    s.logon_time,",
                    "    s.module,",
                    "    s.action,",
                    "    s.client_info,",
                    "    s.event,",
                    "    s.wait_class,",
                    "    s.seconds_in_wait,",
                    "    s.state,",
                    "    s.sql_id,",
                    "    q.sql_text",
                    "FROM",
                    "    sys.v$session s",
                    "LEFT JOIN",
                    "    sys.v$sql q",
                    "    ON s.sql_id = q.sql_id",
                    "WHERE s.status = 'ACTIVE'",
                    "ORDER BY",
                    "    s.sid"
                ]
            )
        
        if category == "locks":
            return "\n".join(
                [
                    "SELECT",
                    "    waiting_session.sid AS wait_sid,",
                    "    waiting_session.username AS wait_user,",
                    "    holding_session.sid AS hold_sid,",
                    "    holding_session.username AS hold_user,",
                    "    waiting_sql.sql_text AS wait_statement,",
                    "    holding_sql.sql_text AS hold_statement",
                    "FROM",
                    "    sys.v$lock waiting_lock",
                    "JOIN",
                    "    sys.v$session waiting_session",
                    "    ON waiting_lock.sid = waiting_session.sid",
                    "JOIN",
                    "    sys.v$lock holding_lock",
                    "    ON waiting_lock.id1 = holding_lock.id1",
                    "    AND waiting_lock.id2 = holding_lock.id2",
                    "    AND holding_lock.block = 1",
                    "JOIN",
                    "    sys.v$session holding_session",
                    "    ON holding_lock.sid = holding_session.sid",
                    "LEFT JOIN",
                    "    sys.v$sql waiting_sql",
                    "    ON waiting_session.sql_id = waiting_sql.sql_id",
                    "LEFT JOIN",
                    "    sys.v$sql holding_sql",
                    "    ON holding_session.sql_id = holding_sql.sql_id",
                    "WHERE",
                    "    waiting_lock.block = 0",
                    "    AND waiting_lock.request > 0",
                    "ORDER BY",
                    "    wait_sid"
                ]
            )

    def meta(self, type, target, path):
        sql = None
        params = None
        meta = { "type": None, "color": None, "class": None, "children": True, "menu_items": [] }

        if type == "database-list":
            meta["type"] = "database-list"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            sql = self._sql("schemas")
            params = self.schemas if isinstance(self.schemas, list) and len(self.schemas) > 0 else None

        if type == "schema-list":
            meta["type"] = "schema-list"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            # Oracle only uses Schemas
            return meta, None

        if type == "connection":
            meta["type"] = "db-folder"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Schemas"]
        
        if type == "db-folder":
            meta["type"] = "database"
            meta["color"] = "purple"
            meta["classes"] = ["fas", "fa-file-lines"]
            meta["menu_items"] = ["refresh", "tab", "copy"]

            sql = self._sql("schemas")
            params = self.schemas if isinstance(self.schemas, list) and len(self.schemas) > 0 else None

        if type == "database":
            meta["type"] = "schema-folder"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Tables", "Views", "Materialized Views", "Sequences", "Functions", "Packages", "Procedures"]

        if type == "schema-folder" and target == "Tables":
            meta["type"] = "table"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("tables")
            params = [path.get("database"), path.get("database")]

        if type == "schema-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("views")
            params = [path.get("database")]

        if type == "schema-folder" and target == "Materialized Views":
            meta["type"] = "mat_view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("mat_views")
            params = [path.get("database")]

        if type == "schema-folder" and target == "Sequences":
            meta["type"] = "sequence"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["copy", "ddl", "details"]

            sql = self._sql("sequences")
            params = [path.get("database")]

        if type == "schema-folder" and target in ["Functions", "Packages", "Procedures"]:
            meta["type"] = "function" if target == "Functions" else "package" if target == "Packages" else "procedure"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["copy", "ddl", "details"]

            sql = self._sql("functions")
            params = [meta.get("type").upper(), path.get("database")]

        if type == "table":
            meta["type"] = "table-folder"
            meta["color"] = "orange"
            meta["classes"] = ["far", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Columns", "Constraints", "Indexes", "Partitions", "Triggers"]
        
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

            return meta, ["Columns", "Indexes"]

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

            sql = self._sql("columns")
            params = [path.get("database"), path.get("view")]

        if type == "mat_view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("columns")
            params = [path.get("database"), path.get("mat_view")]

        if type == "mat_view-folder" and target == "Indexes":
            meta["type"] = "index"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("indexes")
            params = [path.get("database"), path.get("mat_view")]

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

        if type == "table-folder" and target == "Partitions":
            meta["type"] = "partition"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["children"] = True
            meta["menu_items"] = ["refresh", "copy"]

            sql = self._sql("partitions")
            params = [path.get("database"), path.get("table")]

        if type == "table-folder" and target == "Triggers":
            meta["type"] = "trigger"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("triggers")
            params = [path.get("database"), path.get("table")]

        if type == "partition":
            meta["type"] = "part-folder"
            meta["color"] = "orange"
            meta["classes"] = ["far", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Subpartitions"]

        if type == "part-folder" and target == "Subpartitions":
            meta["type"] = "subpartition"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["children"] = True
            meta["menu_items"] = ["refresh", "copy"]

            sql = self._sql("subpartitions")
            params = [path.get("database"), path.get("table"), path.get("partition")]

        records = []

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                records.append(str(record[0]))

        return meta, records
    
    def ddl(self, type, target, path):
        sql = None
        params = None
        meta = { "type": None }

        if type == "table":
            meta["type"] = "table"

            sql = self._sql("ddl")
            params = ['TABLE', target, path.get("database")]

        if type == "view":
            meta["type"] = "view"

            sql = self._sql("ddl")
            params = ['VIEW', target, path.get("database")]

        if type == "mat_view":
            meta["type"] = "mat_view"

            sql = self._sql("ddl")
            params = ['MATERIALIZED_VIEW', target, path.get("database")]

        if type == "sequence":
            meta["type"] = "sequence"

            sql = self._sql("ddl")
            params = ['SEQUENCE', target, path.get("database")]

        if type == "function":
            meta["type"] = "function"

            sql = self._sql("ddl")
            params = ['FUNCTION', target, path.get("database")]

        if type == "procedure":
            meta["type"] = "procedure"

            sql = self._sql("ddl")
            params = ['PROCEDURE', target, path.get("database")]

        if type == "constraint":
            meta["type"] = "constraint"

            sql = self._sql("ddl")
            params = ['CONSTRAINT', target, path.get("database")]

        if type == "index":
            meta["type"] = "index"

            sql = self._sql("ddl")
            params = ['INDEX', target, path.get("database")]

        if type == "trigger":
            meta["type"] = "trigger"

            sql = self._sql("ddl")
            params = ['TRIGGER', target, path.get("database")]

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
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("table")
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[1],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[0],
                })

                data["meta"].append({
                    "name": "Tablespace",
                    "value": record[2],
                })

            sql = self._sql("ddl")
            params = ["TABLE", target, path.get("database")]
            for _, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("columns")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self._sql("grants")
            params = ["TABLE", path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type == "view":
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("view")
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[1],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[0],
                })

                data["meta"].append({
                    "name": "Read Only",
                    "value": record[2],
                })

            sql = self._sql("ddl")
            params = ["VIEW", target, path.get("database")]
            for _, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("columns")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self._sql("grants")
            params = ["VIEW", path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type == "mat_view":
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("mat_view")
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[1],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[0],
                })

                data["meta"].append({
                    "name": "Updatable",
                    "value": record[2],
                })

                data["meta"].append({
                    "name": "Refresh Mode",
                    "value": record[3],
                })

                data["meta"].append({
                    "name": "Refresh Method",
                    "value": record[4],
                })

                data["meta"].append({
                    "name": "Last Refresh",
                    "value": record[5],
                })

            sql = self._sql("ddl")
            params = ["MATERIALIZED_VIEW", target, path.get("database")]
            for _, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("columns")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self._sql("grants")
            params = ["TABLE", path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type == "sequence":
            data = { 
                "meta": [], 
                "sections": {
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("sequence")
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[1],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[0],
                })

                data["meta"].append({
                    "name": "Min Value",
                    "value": record[2],
                })

                data["meta"].append({
                    "name": "Max Value",
                    "value": record[3],
                })

                data["meta"].append({
                    "name": "Increment By",
                    "value": record[4],
                })

                data["meta"].append({
                    "name": "Cache Size",
                    "value": record[5],
                })

                data["meta"].append({
                    "name": "Last Value",
                    "value": record[6],
                })

            sql = self._sql("ddl")
            params = ["SEQUENCE", target, path.get("database")]
            for _, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("grants")
            params = ["SEQUENCE", path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type in ["function", "procedure", "package"]:
            data = { 
                "meta": [], 
                "sections": {
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            query_val = "FUNCTION" if type.upper() == "FUNCTION" else "PROCEDURE" if type.upper() == "PROCEDURE" else "PACKAGE"

            sql = self._sql("function")
            params = [query_val, path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({
                    "name": "Name",
                    "value": record[1],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[0],
                })

            sql = self._sql("ddl")
            params = [query_val, target, path.get("database")]
            for _, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("grants")
            params = [query_val, path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        return data