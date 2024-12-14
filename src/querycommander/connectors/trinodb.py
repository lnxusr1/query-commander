import sys
from datetime import datetime
from decimal import Decimal
import time
import trino
from querycommander.connectors import Connector

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

                sql = sql.rstrip(";")

                if params is None or len(params) == 0:
                    cur.execute(sql)
                else:
                    cur.execute(sql, params)
                self.stats["exec_time"] = time.time()

                return cur
            except trino.exceptions.TrinoUserError as e:
                raise Exception(e.message)
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
                    headers = [{ "name": desc.name, "type": "text" } for desc in cur.description]
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

            sql = self.get_sql_file("databases")
            params = self.databases if isinstance(self.databases, list) and len(self.databases) > 0 else None

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

            sql = self.get_sql_file("databases")
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

            sql = self.get_sql_file("schemas")
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

            sql = self.get_sql_file("tables")
            params = [path.get("schema")]

        if type == "schema-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl"]

            sql = self.get_sql_file("views")
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

            sql = self.get_sql_file("columns")
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

            sql = self.get_sql_file("view")
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
                    "Source": { "type": "code", "data": self.get_sql_file(type) }
                }
            }

        if type == "table":
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Permissions": { "type": "table", "headers": [], "records": [] } #,
                }
            }

            sql = self.get_sql_file("table-detail")
            params = [path["schema"], target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Type", "value": record[3] })
                data["meta"].append({ "name": "Catalog", "value": record[0] })
                data["meta"].append({ "name": "Schema", "value": record[1] })

            sql = self.get_sql_file("columns")
            params = [path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            try:
                sql = self.get_sql_file("table-privs")
                params = [path["schema"], target]
                for headers, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Permissions"]["headers"] = headers
                    data["sections"]["Permissions"]["records"].append(record)
            except:
                pass

        return data
