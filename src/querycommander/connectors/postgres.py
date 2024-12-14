import sys
from datetime import datetime
from decimal import Decimal
import time
import pg8000
import pg8000.dbapi
from querycommander.connectors import Connector
from querycommander.core.helpers import quote_ident

class Postgres(Connector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._type = "postgres"

        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port", 5432)
        self.options = kwargs.get("options", {})
        if "application_name" not in self.options:
            self.options["application_name"] = f"Query Commander [{str(self.tokenizer.username)[0:50]}]"
        
        self.user = kwargs.get("username")
        self.password = kwargs.get("password")
        self.database = kwargs.get("database")
        self.databases = kwargs.get("databases")

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
            
            if len(headers) == 0 or (str(query_type).lower() != "explain" and cur.rowcount <= 0):
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

    def _sql(self, category):
        category = str(category).lower().strip()
        
        if category == "databases":
            if isinstance(self.databases, list) and len(self.databases) > 0:
                in_str = []
                for i in range(0,len(self.databases)):
                    in_str.append("%s")

                return f"select datname from pg_catalog.pg_database where not datistemplate and datname in ({', '.join(in_str)}) order by datname"
            else:
                return "select datname from pg_catalog.pg_database where not datistemplate order by datname"
        
        return self.get_sql_file(category)

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

            return meta, ["Schemas", "Roles"]
        
        if type == "db-folder" and target == "Schemas":
            meta["type"] = "schema"
            meta["color"] = "purple"
            meta["classes"] = ["fas", "fa-file-lines"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details", "tab"]

            sql = self._sql("schemas")
            params = None

        if type == "db-folder" and target == "Roles":
            meta["type"] = "role"
            meta["color"] = "gray"
            meta["classes"] = ["fas", "fa-user"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "details"]
 
            sql = self._sql("roles")
            params = None

        if type == "schema":
            meta["type"] = "schema-folder"
            meta["color"] = "orange"
            meta["classes"] = ["fas", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Tables", "Views", "Materialized Views", "Sequences", "Functions", "Procedures"]
        
        if type == "schema-folder" and target == "Tables":
            meta["type"] = "table"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("tables")
            params = [path.get("schema")]

        if type == "schema-folder" and target == "Views":
            meta["type"] = "view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-layer-group"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("views")
            params = [path.get("schema")]

        if type == "schema-folder" and target == "Materialized Views":
            meta["type"] = "mat_view"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("mat_views")
            params = [path.get("schema")]

        if type == "schema-folder" and target == "Sequences":
            meta["type"] = "sequence"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-hashtag"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl", "details"]

            sql = self._sql("sequences")
            params = [path.get("schema")]

        if type == "schema-folder" and target == "Functions":
            meta["type"] = "function"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl", "details"]

            sql = self._sql("functions")
            params = [path.get("schema")]

        if type == "schema-folder" and target == "Procedures":
            meta["type"] = "procedure"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-code-fork"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl", "details"]

            sql = self._sql("procedures")
            params = [path.get("schema")]

        if type == "table":
            meta["type"] = "table-folder"
            meta["color"] = "orange"
            meta["classes"] = ["far", "fa-folder"]
            meta["menu_items"] = ["refresh"]

            return meta, ["Columns", "Constraints", "Indexes", "Policies", "Partitions", "Triggers"]
        
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
            params = [path.get("schema"), path.get("table")]

        if type == "view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("columns")
            params = [path.get("schema"), path.get("view")]

        if type == "mat_view-folder" and target == "Columns":
            meta["type"] = "column"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-columns"]
            meta["children"] = False
            meta["menu_items"] = ["copy"]

            sql = self._sql("columns")
            params = [path.get("schema"), path.get("mat_view")]

        if type == "mat_view-folder" and target == "Indexes":
            meta["type"] = "index"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("indexes")
            params = [path.get("schema"), path.get("mat_view")]

        if type == "table-folder" and target == "Constraints":
            meta["type"] = "constraint"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("constraints")
            params = [path.get("schema"), path.get("table")]

        if type == "table-folder" and target == "Indexes":
            meta["type"] = "index"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("indexes")
            params = [path.get("schema"), path.get("table")]

        if type == "table-folder" and target == "Policies":
            meta["type"] = "policy"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("policies")
            params = [path.get("schema"), path.get("table")]

        if type == "table-folder" and target == "Partitions":
            meta["type"] = "table"
            meta["color"] = "navy"
            meta["classes"] = ["fas", "fa-table"]
            meta["children"] = True
            meta["menu_items"] = ["refresh", "copy", "ddl", "details"]

            sql = self._sql("partitions")
            params = [path.get("schema"), path.get("table")]

        if type == "table-folder" and target == "Triggers":
            meta["type"] = "trigger"
            meta["color"] = "purple"
            meta["classes"] = ["far", "fa-file-lines"]
            meta["children"] = False
            meta["menu_items"] = ["copy", "ddl"]

            sql = self._sql("triggers")
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

        if type == "schema":
            meta["type"] = "schema"

            sql = self._sql("schema")
            params = [target]

        if type in ["table", "partition"]:
            meta["type"] = "table"

            sql = self._sql("table")
            params = [path["schema"], target]

        if type == "view":
            meta["type"] = "view"

            sql = self._sql("view")
            params = [path["schema"], path["view"]]

        if type == "mat_view":
            meta["type"] = "mat_view"

            sql = self._sql("mat_view")
            params = [path["schema"], path["mat_view"]]

        if type == "sequence":
            meta["type"] = "sequence"

            sql = self._sql("sequence")
            params = [path["schema"], path["sequence"]]

        if type == "policy":
            meta["type"] = "policy"

            sql = self._sql("policy")
            params = [path["schema"], path["table"], path["policy"]]

        if type == "trigger":
            meta["type"] = "trigger"
            
            sql = self._sql("trigger")
            params = [path["schema"], path["table"], path["trigger"]]

        if type == "function":
            meta["type"] = "function"

            sql = self._sql("function")
            params = [path["schema"], path["function"]]

        if type == "procedure":
            meta["type"] = "procedure"

            sql = self._sql("procedure")
            params = [path["schema"], path["procedure"]]

        if type == "index":
            meta["type"] = "index"

            sql = self._sql("index")
            params = [path["schema"], path["index"]]

        if type == "constraint":
            meta["type"] = "constraint"

            sql = self._sql("constraint")
            params = [path["schema"], path["constraint"]]

        if type == "partition":
            meta["type"] = "partition"

            sql = self._sql("partition")
            params = [path["schema"], path["partition"]]

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

        if type == "schema":
            data = { 
                "meta": [], 
                "sections": {
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("schema")
            params = [target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[1] })
                data["meta"].append({ "name": "Owner", "value": record[2] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("grants")
            params = ["schema", record[1], record[1]]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type == "table":
            data = { 
                "meta": [], 
                "sections": {
                    "Columns": { "type": "table", "headers": [], "records": [] },
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("table-detail")
            params = [path["schema"], target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[1] })
                data["meta"].append({ "name": "Owner", "value": record[2] })
                data["meta"].append({ "name": "Schema", "value": record[0] })
                data["meta"].append({ "name": "Tablespace", "value": record[3] })
                data["meta"].append({ "name": "RLS Enabled", "value": record[4] })

            sql = self._sql("columns")
            params = [path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self._sql("grants")
            params = ["table", path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

            sql = self._sql("table")
            params = [path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Source"]["data"] = record[0]
    
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
            params = [path["schema"], target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("columns")
            params = [path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self._sql("grants")
            params = ["view", path["schema"], target]
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
            params = [path["schema"], target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })
                data["meta"].append({ "name": "Tablespace", "value": record[4] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("columns")
            params = [path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Columns"]["headers"] = headers
                data["sections"]["Columns"]["records"].append(record)

            sql = self._sql("grants")
            params = ["materialized view", path["schema"], target]
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
            params = [path["schema"], target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })
                data["meta"].append({ "name": "Last Value", "value": record[4] })
                data["meta"].append({ "name": "Data Type", "value": record[5] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("grants")
            params = ["sequence", path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type in ["function", "procedure"]:
            data = { 
                "meta": [], 
                "sections": {
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql(type)
            params = [path["schema"], target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })                
                data["meta"].append({ "name": "Language", "value": record[4] })
                data["meta"].append({ "name": "Arguments", "value": record[5] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("grants")
            params = [type, path["schema"], target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        if type == "role":
            data = { 
                "meta": [], 
                "sections": {
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql(type)
            params = [target]

            for _, record in self.fetchmany(sql, params, 1000):
                data["meta"].append({ "name": "Name", "value": record[2] })
                data["meta"].append({ "name": "Owner", "value": record[3] })
                data["meta"].append({ "name": "Schema", "value": record[1] })                
                data["meta"].append({ "name": "Language", "value": record[4] })
                data["meta"].append({ "name": "Arguments", "value": record[5] })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("role-grants")
            params = [target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        return data        