import sys
from datetime import datetime
from decimal import Decimal
import time
import pg8000
import pg8000.dbapi
from querycommander.connectors import Connector
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
                    **self.options
                )

                self.connection.autocommit = True

            except:
                self.log(sys.exc_info()[0], message="Unable to connect to database.", with_trace=True)
                self.connection = None
                return False

        return True
    
    def commit(self):
        if self.connection is not None:
            try:
                self.connection.commit()
            except:
                self.log(sys.exc_info()[0], message="Unable to commit transaction.", with_trace=True)
                return False
        
        return True

    def close(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except:
                self.log(sys.exc_info()[0], message="Unable to close database connection.", with_trace=True)
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
                    cur.execute(f"SET search_path TO {quote_ident(self.schema)};")

                if params is None or len(params) == 0:
                    cur.execute(sql)
                else:
                    cur.execute(sql, params)
                self.stats["exec_time"] = time.time()

                return cur
            except pg8000.dbapi.ProgrammingError as e:
                raise Exception(e.args[0]['M'])
            except:
                self.log(sys.exc_info()[0], message="Query execution failed.", with_trace=True)
                raise
            
        else:
            self.log("Unable to establish connection", with_trace=False)
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
                self.logger.debug(str(sql))
                self.log(sys.exc_info()[0], message="Unable to parse columns.", with_trace=True)
                headers = []
            except:
                self.logger.debug(str(sql))
                self.log(sys.exc_info()[0], message="Unable to parse columns.", with_trace=True)
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
            except:
                self.log(sys.exc_info()[0], message="Unable to fetch rows for query.", with_trace=True)
                self.stats["end_time"] = time.time()
                raise

            try:
                cur.close()
            except:
                self.log(sys.exc_info()[0], message="Unable to close cursor for query.", with_trace=True)
                self.stats["end_time"] = time.time()
                raise

        else:
            self.log("Unable to establish connection", with_trace=False)
            self.stats["end_time"] = time.time()
            raise ConnectionError("Unable to establish connection")

        self.stats["end_time"] = time.time()

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

            sql = self.get_sql_file("schemas")
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

            sql = self.get_sql_file("schemas")
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

            sql = self.get_sql_file("tables")
            params = [path.get("database")]

        if type == "schema-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self.get_sql_file("views")
            params = [self.database, path.get("database")]

        if type == "schema-folder" and target == "Materialized Views":
            meta["type"] = "mat_view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self.get_sql_file("mat_views")
            params = [self.database, path.get("database")]

        if type == "schema-folder" and target == "Procedures":
            meta["type"] = "procedure"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code-fork"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self.get_sql_file("functions")
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

            sql = self.get_sql_file("columns")
            params = [path.get("database"), path.get("table")]

        if type == "view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self.get_sql_file("view-columns")
            params = [path.get("database"), path.get("view").rstrip()]

        if type == "mat_view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self.get_sql_file("view-columns")
            params = [path.get("database"), path.get("mat_view").rstrip()]

        if type == "table-folder" and target == "Constraints":
            meta["type"] = "constraint"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self.get_sql_file("constraints")
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

            sql = self.get_sql_file("schema")
            params = [target]

        if type == "table":
            meta["type"] = "table"

            sql = self.get_sql_file("table")
            params = [path.get("database"), target]

        if type == "view":
            meta["type"] = "view"

            sql = self.get_sql_file("view")
            params = [path.get("database"), path.get("view").rstrip()]

        if type == "mat_view":
            meta["type"] = "mat_view"

            sql = self.get_sql_file("mat_view")
            params = [path.get("database"), path.get("mat_view").rstrip()]

        if type == "procedure":
            meta["type"] = "procedure"

            sql = self.get_sql_file("procedure")
            params = [path.get("database"), path.get("procedure")]

        if type == "constraint":
            meta["type"] = "constraint"

            sql = self.get_sql_file("constraint")
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
                    "Source": { "type": "code", "data": self.get_sql_file(type) }
                }
            }

        if type == "table":
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self.get_sql_file("table-detail")
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[1] })
                data["meta"].append({ "name": "Owner", "value": record[2] })
                data["meta"].append({ "name": "Schema", "value": record[0] })
                data["meta"].append({ "name": "Tablespace", "value": record[3] })

            sql = self.get_sql_file("columns")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self.get_sql_file("table")
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

            sql = self.get_sql_file("view")
            params = [path.get("database"), target.rstrip()]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self.get_sql_file("view-columns")
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

            sql = self.get_sql_file("mat_view")
            params = [path.get("database"), target.rstrip()]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self.get_sql_file("view-columns")
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

            sql = self.get_sql_file(type)
            params = [path.get("database"), target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })                
                data["meta"].append({ "name": "Language", "value": record[4] })
                data["meta"].append({ "name": "Arguments", "value": record[5] })

                data["sections"]["Source"]["data"] = record[0]

        return data
        