import sys
from datetime import datetime
from decimal import Decimal
import time
import mysql.connector
from mysql.connector import errorcode
from querycommander.connectors import Connector


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
                    self.log(sys.exc_info()[0], message="Invalid username or password.", with_trace=True)
                    self.connection = None
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    self.log(sys.exc_info()[0], message="Selected database does not exist.", with_trace=True)
                    self.connection = None
                else:
                    self.log(sys.exc_info()[0], message="Unable to connect to database.", with_trace=True)
                    self.connection = None

                return False
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
                cur.execute(sql, params=params)
                self.stats["exec_time"] = time.time()

                return cur
            except:
                self.log(sys.exc_info()[0], message="Query execution failed.", with_trace=True)
                raise
            
        else:
            self.log("Unable to establish connection.", with_trace=False)
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
                    records = cur.fetchmany(size=size)
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
            self.log("Unable to establish connection.", with_trace=True)
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
            params = None

        if type == "schema-list":
            meta["type"] = "schema-list"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, None

        if type == "connection":
            meta["type"] = "database"
            meta["color"] = "brown"
            meta["classes"] = ["fa", "fa-database"]
            meta["menu_items"] = ["refresh", "tab", "copy", "ddl", "details"]

            sql = self.get_sql_file("databases")
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

            sql = self.get_sql_file("tables")
            params = [path.get("database")]

        if type == "db-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self.get_sql_file("views")
            params = [path.get("database")]

        if type == "db-folder" and target == "Functions":
            meta["type"] = "function"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self.get_sql_file("functions")
            params = [path.get("database")]

        if type == "db-folder" and target == "Procedures":
            meta["type"] = "procedure"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code-fork"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self.get_sql_file("procedures")
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

            sql = self.get_sql_file("columns")
            params = [path.get("database"), path.get("table")]

        if type == "table-folder" and target == "Constraints":
            meta["type"] = "constraint"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self.get_sql_file("constraints")
            params = [path.get("database"), path.get("table")]

        if type == "table-folder" and target == "Indexes":
            meta["type"] = "index"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self.get_sql_file("indexes")
            params = [path.get("database"), path.get("table")]

        if type == "table-folder" and target == "Triggers":
            meta["type"] = "trigger"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self.get_sql_file("triggers")
            params = [path.get("database"), path.get("table")]

        if type == "view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self.get_sql_file("columns")
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

            sql = self.get_sql_file("databases")
            params = None

            for _, record in self.fetchmany(sql, params, 1000):
                if record[0] == target:
                    statement = f"CREATE DATABASE `{record[0]}`;"

                    return meta, statement
            
            return meta, ""

        if type == "table":
            meta["type"] = "table"
            code_column = 1

            sql = self.get_sql_file("table").format(OBJECT_NAME=target)
            params = None

        if type == "view":
            meta["type"] = "view"
            code_column = 1

            sql = self.get_sql_file("view").format(OBJECT_NAME=target)
            params = None

        if type in ["index", "constraint"]:
            meta["type"] = type
            code_column = 1

            sql = self.get_sql_file("table").format(OBJECT_NAME=path.get("table"))
            params = None

        if type == "function":
            meta["type"] = "function"
            code_column = 2

            sql = self.get_sql_file("function").format(OBJECT_NAME=target)
            params = None

        if type == "procedure":
            meta["type"] = "procedure"
            code_column = 2

            sql = self.get_sql_file("procedure").format(OBJECT_NAME=target)
            params = None

        if type == "trigger":
            meta["type"] = "trigger"
            code_column = 2

            sql = self.get_sql_file("trigger").format(OBJECT_NAME=target)
            params = None

        if sql is not None:
            for _, record in self.fetchmany(sql, params, 1000):
                statement = str(record[code_column])

        return meta, statement
    
    def details(self, type, target, path):
        sql = None
        params = None
        data = None

        if type in ["sessions"]:
            data = {
                "meta": [], 
                "sections": {
                    "Source": { "type": "code", "data": self.get_sql_file(type) }
                }
            }

        if type in ["locks"]:
            locks_query = "locks-perf"
            for headers, record in self.fetchmany("show variables like 'performance_schema'"):
                if str(record[0]).lower() == "performance_schema":
                    if str(record[1].lower()) == "off":
                        locks_query = "locks-innodb"

            data = {
                "meta": [], 
                "sections": {
                    "Source": { "type": "code", "data": self.get_sql_file(locks_query) }
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

            sql = self.get_sql_file("databases")
            params = None

            schema_name = None
            for _, record in self.fetchmany(sql, params, 1000):
                if record[0] == target:
                    schema_name = record[0]
                    data["meta"].append({ "name": "Name", "value": schema_name })

                    data["sections"]["Source"]["data"] = f"CREATE DATABASE `{schema_name}`;"

            if schema_name is not None:
                sql = self.get_sql_file("schema-grants")
                params = [schema_name]
                for headers, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Schema Permissions"]["headers"] = headers
                    data["sections"]["Schema Permissions"]["records"].append(record)

                sql = self.get_sql_file("global-grants")
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

            sql = self.get_sql_file("table-info")
            params = [path.get("database"), target]

            table_name = None
            for _, record in self.fetchmany(sql, params, 1000):
                table_name = record[1]
                data["meta"].append({ "name": "Name", "value": table_name })
                data["meta"].append({ "name": "Type", "value": record[4] })
                data["meta"].append({ "name": "Schema", "value": record[0] })
                data["meta"].append({ "name": "Engine", "value": record[3] })
                data["meta"].append({ "name": "Collation", "value": record[2] })

            if table_name is not None:
                sql = self.get_sql_file("table").format(OBJECT_NAME=table_name)
                params = None
                for _, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Source"]["data"] = record[1]

            sql = self.get_sql_file("grants")
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

            sql = self.get_sql_file("view-info")
            params = [path.get("database"), target]

            table_name = None
            for _, record in self.fetchmany(sql, params, 1000):
                table_name = record[1]
                data["meta"].append({ "name": "Name", "value": table_name, })
                data["meta"].append({ "name": "Type", "value": record[4] })
                data["meta"].append({ "name": "Schema", "value": record[0] })

            if table_name is not None:
                sql = self.get_sql_file("view").format(OBJECT_NAME=table_name)
                params = None
                for _, record in self.fetchmany(sql, params, 1000):
                    data["sections"]["Source"]["data"] = record[1]

            sql = self.get_sql_file("grants")
            params = [path.get("database"), target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)
    
        return data