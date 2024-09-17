import os
import sys
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
        #return "\n".join([str(x) for x in self._notices])

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
            if isinstance(self.databases, list) and len(self.databases) > 0:
                in_str = []
                for i in range(0,len(self.databases)):
                    in_str.append("%s")

                return f"select datname from pg_catalog.pg_database where not datistemplate and datname in ({', '.join(in_str)}) order by datname"
            else:
                return "select datname from pg_catalog.pg_database where not datistemplate order by datname"
        
        if category == "schemas":
            return "select nspname from pg_catalog.pg_namespace where nspname not in ('pg_catalog', 'pg_toast', 'information_schema') order by nspname"
        
        if category == "schema":
            return "select CONCAT('CREATE SCHEMA ', nspname, ' AUTHORIZATION ', nspowner::regrole::text, ';') as definition, nspname, nspowner::regrole::text as nspowner from pg_catalog.pg_namespace where nspname = %s"

        if category == "tables":
            return " ".join(
                [
                    "select tablename from (",
                    "select nspname as schemaname, relname as tablename from pg_catalog.pg_class",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where pg_class.oid in (select partrelid from pg_catalog.pg_partitioned_table)",
                    "and pg_class.oid not in (select inhrelid from pg_catalog.pg_inherits)",
                    "union",
                    "select pg_tables.schemaname, pg_tables.tablename from pg_catalog.pg_tables",
                    "join pg_catalog.pg_namespace on pg_tables.schemaname = pg_namespace.nspname",
                    "join pg_catalog.pg_class on pg_tables.tablename = pg_class.relname and pg_namespace.oid = pg_class.relnamespace",
                    "where pg_class.oid not in (select partrelid from pg_catalog.pg_partitioned_table)",
                    "and pg_class.oid not in (select inhrelid from pg_catalog.pg_inherits)",
                    ") x where schemaname = %s order by tablename"
                ]
            )
        
        if category in ["table-detail", "partition-detail"]:
            return " ".join(
                [
                    "select schemaname, tablename, tableowner, tablespace, rowsecurity from pg_catalog.pg_tables where schemaname = %s and tablename = %s"
                ]
            )

        if category in ["table", "partition"]:
            with open(os.path.join(os.path.dirname(__file__), 'extra_sql', 'postgres_table.sql'), "r", encoding="UTF_8") as fp:
                sql = fp.read()
            return sql
        
            return " ".join(
                [
                    "WITH table_oid as (select CONCAT(schema_name, '.', table_name)::regclass as oid from (select %s as schema_name, %s as table_name) x), ",
                    "attrdef AS (",
                    "    SELECT",
                    "        n.nspname,",
                    "        c.relname,",
                    "        pg_catalog.array_to_string(c.reloptions || array(select 'toast.' || x from pg_catalog.unnest(tc.reloptions) x), ', ') as relopts,",
                    "        c.relpersistence,",
                    "        a.attnum,",
                    "        a.attname,",
                    "        pg_catalog.format_type(a.atttypid, a.atttypmod) as atttype,",
                    "        (SELECT substring(pg_catalog.pg_get_expr(d.adbin, d.adrelid, true) for 128) FROM pg_catalog.pg_attrdef d",
                    "            WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef) as attdefault,",
                    "        a.attnotnull,",
                    "        (SELECT c.collname FROM pg_catalog.pg_collation c, pg_catalog.pg_type t",
                    "            WHERE c.oid = a.attcollation AND t.oid = a.atttypid AND a.attcollation <> t.typcollation) as attcollation,",
                    "        a.attidentity,",
                    "        a.attgenerated",
                    "    FROM pg_catalog.pg_attribute a",
                    "    JOIN pg_catalog.pg_class c ON a.attrelid = c.oid",
                    "    JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid",
                    "    LEFT JOIN pg_catalog.pg_class tc ON (c.reltoastrelid = tc.oid)",
                    "    WHERE a.attrelid = (select oid from table_oid limit 1)::regclass",
                    "        AND a.attnum > 0",
                    "        AND NOT a.attisdropped",
                    "    ORDER BY a.attnum"
                    "),",
                    "coldef AS (",
                    "    SELECT",
                    "        attrdef.nspname,",
                    "        attrdef.relname,",
                    "        attrdef.relopts,",
                    "        attrdef.relpersistence,",
                    "        pg_catalog.format(",
                    "            '%%I %%s%%s%%s%%s%%s',",
                    "            attrdef.attname,",
                    "            attrdef.atttype,",
                    "            case when attrdef.attcollation is null then '' else pg_catalog.format(' COLLATE %%I', attrdef.attcollation) end,",
                    "            case when attrdef.attnotnull then ' NOT NULL' else '' end,",
                    "            case when attrdef.attdefault is null then ''",
                    "                else case when attrdef.attgenerated = 's' then pg_catalog.format(' GENERATED ALWAYS AS (%%s) STORED', attrdef.attdefault)",
                    "                    when attrdef.attgenerated <> '' then ' GENERATED AS NOT_IMPLEMENTED'",
                    "                    else pg_catalog.format(' DEFAULT %%s', attrdef.attdefault)",
                    "                end",
                    "            end,",
                    "            case when attrdef.attidentity<>'' then pg_catalog.format(' GENERATED %%s AS IDENTITY',",
                    "                    case attrdef.attidentity when 'd' then 'BY DEFAULT' when 'a' then 'ALWAYS' else 'NOT_IMPLEMENTED' end)",
                    "                else '' end",
                    "        ) as col_create_sql",
                    "    FROM attrdef",
                    "    ORDER BY attrdef.attnum"
                    "),",
                    "tabdef AS (",
                    "    SELECT",
                    "        coldef.nspname,",
                    "        coldef.relname,",
                    "        coldef.relopts,",
                    "        coldef.relpersistence,",
                    "        string_agg(coldef.col_create_sql, E',\\n    ') as cols_create_sql",
                    "    FROM coldef",
                    "    GROUP BY",
                    "        coldef.nspname, coldef.relname, coldef.relopts, coldef.relpersistence",
                    ")",
                    "SELECT",
                    "    format(",
                    "        'CREATE%%s TABLE %%I.%%I%%s%%s%%s;',",
                    "        case tabdef.relpersistence when 't' then ' TEMP' when 'u' then ' UNLOGGED' else '' end,",
                    "        tabdef.nspname,",
                    "        tabdef.relname,",
                    "        coalesce(",
                    "            (SELECT format(E'\\n    PARTITION OF %%I.%%I %%s\\n', pn.nspname, pc.relname,",
                    "                pg_get_expr(c.relpartbound, c.oid))",
                    "                FROM pg_class c JOIN pg_inherits i ON c.oid = i.inhrelid",
                    "                JOIN pg_class pc ON pc.oid = i.inhparent",
                    "                JOIN pg_namespace pn ON pn.oid = pc.relnamespace",
                    "                WHERE c.oid = (select oid from table_oid limit 1)::regclass),",
                    "            format(E' (\\n    %%s\\n)', tabdef.cols_create_sql)",
                    "        ),",
                    "        case when tabdef.relopts <> '' then format(' WITH (%%s)', tabdef.relopts) else '' end,",
                    "        coalesce(E'\\nPARTITION BY '||pg_get_partkeydef((select oid from table_oid limit 1)::regclass), '')",
                    "    ) as table_create_sql",
                    "FROM tabdef"
                ]
            )

        if category == "columns":
            return " ".join(
                [
                    "select a.attname as \"Column Name\",",
                    "a.attnum as \"#\", ",
                    "pg_catalog.format_type(a.atttypid, a.atttypmod) as \"Data Type\",",
                    "case when a.attgenerated = 't' and a.attidentity = 't' then true else false end as \"Identity\","
                    "a.attnotnull as \"Not Null\",",
                    "pg_get_expr(d.adbin, d.adrelid) as \"Default\"",
                    "from pg_catalog.pg_attribute a",
                    "join pg_catalog.pg_class t on a.attrelid = t.oid",
                    "left join pg_catalog.pg_attrdef d on (a.attrelid, a.attnum) = (d.adrelid, d.adnum)",
                    "where a.attnum > 0 and not a.attisdropped",
                    "and t.relnamespace::regnamespace::text = %s",
                    "and t.relname = %s",
                    "order by attnum"
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
        
        if category == "constraint":
            return " ".join(
                [
                    "select CONCAT('ALTER TABLE ', pg_namespace.nspname, '.', pg_class.relname, ' ADD CONSTRAINT ', conname, ' ', pg_get_constraintdef(pg_constraint.oid), ';') as definition",
                    "from pg_catalog.pg_constraint",
                    "join pg_catalog.pg_namespace on pg_constraint.connamespace = pg_namespace.oid",
                    "join pg_catalog.pg_class on pg_constraint.conrelid = pg_class.oid",
                    "join pg_catalog.pg_namespace rns on pg_class.relnamespace = rns.oid",
                    "where pg_namespace.nspname = %s and conname = %s;"
                ]
            )
        
        if category == "indexes":
            return " ".join(
                [
                    "select i.relname as \"Index Name\", case when pg_index.indisunique = 't' then true else false end as \"Unique\", CONCAT(pg_get_indexdef(indexrelid),';') as \"Expression\" from pg_catalog.pg_index",
                    "join pg_catalog.pg_class t on pg_index.indrelid = t.oid",
                    "join pg_catalog.pg_namespace on t.relnamespace = pg_namespace.oid",
                    "join pg_catalog.pg_class i on pg_index.indexrelid = i.oid",
                    "where not indisprimary and nspname = %s and t.relname = %s",
                    "order by i.relname"
                ]
            )
        
        if category == "index":
            return " ".join(
                [
                    "select CONCAT(pg_get_indexdef(indexrelid),';') as definition",
                    "from pg_catalog.pg_index",
                    "join pg_catalog.pg_class on pg_index.indexrelid = pg_class.oid",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where nspname = %s and relname = %s;"
                ]
            )

        if category == "views":
            return "select viewname from pg_catalog.pg_views where schemaname = %s order by viewname"
        
        if category == "view":
            return "select CONCAT('CREATE OR REPLACE VIEW ', schemaname, '.', viewname, ' AS \n', definition) as definition, schemaname, viewname, viewowner from pg_catalog.pg_views where schemaname = %s and viewname = %s;"
        
        if category == "mat_views":
            return "select matviewname from pg_catalog.pg_matviews where schemaname = %s order by matviewname"
        
        if category == "mat_view":
            return "select CONCAT('CREATE MATERIALIZED VIEW ', schemaname, '.', matviewname, ' AS \n', definition) as definition, schemaname, matviewname, matviewowner, tablespace from pg_catalog.pg_matviews where schemaname = %s and matviewname = %s;"
        
        if category == "roles":
            return "select rolname from pg_catalog.pg_roles order by rolname"

        if category == "sequences":
            return " ".join(
                [
                    "select relname from pg_catalog.pg_class",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where pg_class.relkind = 'S' and nspname = %s",
                    "order by relname"
                ]
            )
        
        if category == "sequence":
            return " ".join(
                [
                    "select CONCAT('CREATE SEQUENCE IF NOT EXISTS ', schemaname, '.', sequencename, ",
                    "'\n INCREMENT BY ', increment_by, '\n MINVALUE ', min_value, '\n MAXVALUE ', max_value, ",
                    "'\n START WITH ', start_value, '\n CACHE ', cache_size, ",
                    "case when not cycle then '\n NO CYCLE' else '' end, ",
                    "case when owner_table is not null and owner_column is not null then CONCAT('\n OWNED BY ',owner_schema,'.',owner_table,'.',owner_column) else '' end,"
                    "';') as definition, pg_sequences.schemaname, pg_sequences.sequencename, pg_sequences.sequenceowner, pg_sequences.last_value, pg_sequences.data_type",
                    "from pg_catalog.pg_sequences ",
                    "left join (",
                    "select seq.relnamespace::regnamespace::text as seq_schema, seq.relname as seq_name,",
                    "tab.relnamespace::regnamespace::text as owner_schema, ",
                    "tab.relname as owner_table, attr.attname as owner_column",
                    "from pg_class as seq",
                    "join pg_depend as dep on (seq.relfilenode = dep.objid)",
                    "join pg_class as tab on (dep.refobjid = tab.relfilenode)",
                    "join pg_attribute as attr on (attr.attnum = dep.refobjsubid and attr.attrelid = dep.refobjid)",
                    ") o on pg_sequences.schemaname = seq_schema and pg_sequences.sequencename = seq_name",
                    "where schemaname = %s and sequencename = %s"
                ]
            )

        if category == "partitions":
            return " ".join(
                [
                    "select part.relname as partname from pg_catalog.pg_class base_part",
                    "join pg_catalog.pg_inherits i on i.inhparent = base_part.oid",
                    "join pg_catalog.pg_class part on part.oid = i.inhrelid",
                    "where base_part.relnamespace::regnamespace::text = %s and base_part.relname = %s and part.relkind in ('r','p')",
                    "order by part.relname"
                ]
            )
        
        if category == "policies":
            return " ".join(
                [
                    "select polname from pg_catalog.pg_policy",
                    "join pg_catalog.pg_class on pg_policy.polrelid = pg_class.oid",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where nspname = %s and relname = %s",
                    "order by polname"
                ]
            )
        
        if category == "policy":
            return " ".join(
                [
                    "select CONCAT('CREATE POLICY ', polname, chr(10), '    ON ',",
                    "nspname, '.', ",
                    "relname, chr(10), '    AS ',",
                    "case when polpermissive then 'PERMISSIVE' else 'RESTRICTIVE' end, chr(10), '    FOR ',",
                    "case polcmd",
                    "when 'r' then 'SELECT'",
                    "when 'a' then 'INSERT'",
                    "when 'w' then 'UPDATE'",
                    "when 'd' then 'DELETE'",
                    "when '*' then 'ALL'",
                    "else null",
                    "end, chr(10), '    TO ',",
                    "array_to_string(case ",
                    "when polroles = '{0}'::oid[] then string_to_array('public', '')::name[]",
                    "else array(",
                    "select rolname from pg_catalog.pg_roles where oid = ANY(polroles) order by rolname",
                    ") end,', '), chr(10), '    USING (',",
                    "pg_catalog.pg_get_expr(polqual, polrelid, false), ')',",
                    "case when polwithcheck is not null then CONCAT(chr(10), '    WITH CHECK (',",
                    "pg_catalog.pg_get_expr(polwithcheck, polrelid, false), ')') else '' end,",
                    "';') as definition",
                    "from pg_catalog.pg_policy",
                    "join pg_catalog.pg_class on pg_policy.polrelid = pg_class.oid",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where nspname::text = %s and relname::text = %s and polname::text = %s"
                ]
            )
        
        if category == "functions":
            return " ".join(
                [
                    "select concat(proname, '(', pg_catalog.pg_get_function_identity_arguments(pg_proc.oid)::text, ')') as proname from pg_catalog.pg_proc ",
                    "join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid",
                    "where nspname = %s and prokind = 'f' order by proname"
                ]
            )
        
        if category == "procedures":
            return " ".join(
                [
                    "select concat(proname, '(', pg_catalog.pg_get_function_identity_arguments(pg_proc.oid)::text, ')') as proname from pg_catalog.pg_proc ",
                    "join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid",
                    "where nspname = %s and prokind = 'p' order by proname"
                ]
            )

        if category in ["function", "procedure"]:
            return " ".join(
                [
                    "select CONCAT(trim(pg_catalog.pg_get_functiondef(pg_proc.oid)::text), ';') as definition, nspname, proname, proowner::regrole::text as ownername, pg_language.lanname, pg_catalog.pg_get_function_identity_arguments(pg_proc.oid) as arguments",
                    "from pg_catalog.pg_proc",
                    "join pg_catalog.pg_namespace on pg_proc.pronamespace = pg_namespace.oid",
                    "left join pg_catalog.pg_language on pg_proc.prolang = pg_language.oid",
                    "where nspname = %s and CONCAT(proname, '(', pg_catalog.pg_get_function_identity_arguments(pg_proc.oid), ')') = %s"
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
            return "\n".join(
                [
                    "SELECT ",
                    "    pg_stat_activity_waiting.pid AS wait_pid,",
                    "    pg_stat_activity_waiting.usename AS wait_user,",
                    "    pg_stat_activity_holding.pid AS hold_pid,",
                    "    pg_stat_activity_holding.usename AS hold_user,",
                    "    pg_stat_activity_waiting.query AS wait_statement,",
                    "    pg_stat_activity_holding.query AS hold_statement",
                    "FROM ",
                    "    pg_stat_activity AS pg_stat_activity_waiting",
                    "JOIN ",
                    "    pg_locks AS waiting_locks ",
                    "    ON pg_stat_activity_waiting.pid = waiting_locks.pid",
                    "JOIN ",
                    "    pg_locks AS holding_locks ",
                    "    ON waiting_locks.locktype = holding_locks.locktype",
                    "    AND waiting_locks.database IS NOT DISTINCT FROM holding_locks.database",
                    "    AND waiting_locks.relation IS NOT DISTINCT FROM holding_locks.relation",
                    "    AND waiting_locks.page IS NOT DISTINCT FROM holding_locks.page",
                    "    AND waiting_locks.tuple IS NOT DISTINCT FROM holding_locks.tuple",
                    "    AND waiting_locks.virtualxid IS NOT DISTINCT FROM holding_locks.virtualxid",
                    "    AND waiting_locks.transactionid IS NOT DISTINCT FROM holding_locks.transactionid",
                    "    AND waiting_locks.classid IS NOT DISTINCT FROM holding_locks.classid",
                    "    AND waiting_locks.objid IS NOT DISTINCT FROM holding_locks.objid",
                    "    AND waiting_locks.objsubid IS NOT DISTINCT FROM holding_locks.objsubid",
                    "    AND waiting_locks.pid != holding_locks.pid",
                    "JOIN ",
                    "    pg_stat_activity AS pg_stat_activity_holding ",
                    "    ON holding_locks.pid = pg_stat_activity_holding.pid",
                    "WHERE ",
                    "    NOT waiting_locks.granted",
                    "ORDER BY ",
                    "    pg_stat_activity_waiting.pid"
                ]
            )
        
        if category == "roles":
            return "select rolname from pg_catalog.pg_roles order by rolname"
        
        if category == "role":
            return " ".join(
                [
                    "select ",
                    "CONCAT(",
                    "    'CREATE ROLE ', rolname, ' WITH',",
                    "    case when rolsuper = 't' then CONCAT(chr(10), '    SUPERUSER') else '' end,"
                    "    case when rolcreatedb = 't' then CONCAT(chr(10), '    CREATEDB') else '' end,"
                    "    case when rolcreaterole = 't' then CONCAT(chr(10), '    CREATEROLE') else '' end,"
                    "    case when rolinherit = 'f' then CONCAT(chr(10), '    NOINHERIT') else '' end,"
                    "    case when rolcanlogin = 't' then CONCAT(chr(10), '    LOGIN') else '' end,"
                    "    case when rolreplication = 't' then CONCAT(chr(10), '    REPLICATION') else '' end,"
                    "    case when rolbypassrls = 't' then CONCAT(chr(10), '    BYPASSRLS') else '' end,"
                    "    case when rolvaliduntil is not null then CONCAT(chr(10), '    VALID UNTIL ', cast(rolvaliduntil as text)) else '' end,"
                    "    case when rolconnlimit is not null then CONCAT(chr(10), '    CONNECTION LIMIT ', cast(rolconnlimit as text)) else '' end,"
                    "    ';'"
                    ") as definition,"
                    "rolname, ",
                    "case when rolsuper = 't' then true else false end as superuser, ",
                    "case when rolinherit = 't' then true else false end as caninherit, ",
                    "case when rolcreaterole = 't' then true else false end as createrole, ",
                    "case when rolcreatedb = 't' then true else false end as createdb, ",
                    "case when rolcanlogin = 't' then true else false end as canlogin, ",
                    "case when rolreplication = 't' then true else false end as replication, ",
                    "case when rolbypassrls = 't' then true else false end as bypassrls, ",
                    "case when rolconnlimit <= 0 then null else rolconnlimit end as connlimit ",
                    "from pg_catalog.pg_roles where rolname = %s"
                ]
            )
        
        if category == "triggers":
            return " ".join(
                [
                    "select tgname from pg_catalog.pg_trigger",
                    "join pg_catalog.pg_class on pg_trigger.tgrelid = pg_class.oid",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where not tgisinternal and nspname = %s and pg_class.relname = %s",
                    "order by tgname"
                ]
            )
        
        if category == "trigger":
            return " ".join(
                [
                    "select CONCAT(trim(pg_catalog.pg_get_triggerdef(pg_trigger.oid)), ';') as definition",
                    "from pg_catalog.pg_trigger",
                    "join pg_catalog.pg_class on pg_trigger.tgrelid = pg_class.oid",
                    "join pg_catalog.pg_namespace on pg_class.relnamespace = pg_namespace.oid",
                    "where nspname = %s and relname = %s and tgname = %s"
                ]
            )
        
        if category in ["grants", "role-grants"]:
            in_str = " ".join(
                [
                    "WITH rol AS (",
                    "    SELECT oid,",
                    "            rolname::text AS role_name",
                    "        FROM pg_roles",
                    "    UNION",
                    "    SELECT 0::oid AS oid,",
                    "            'public'::text",
                    "),",
                    "schemas AS ( ",
                    "    SELECT oid AS schema_oid,",
                    "            n.nspname::text AS schema_name,",
                    "            n.nspowner AS owner_oid,",
                    "            'schema'::text AS object_type,",
                    "            coalesce ( n.nspacl, acldefault ( 'n'::\"char\", n.nspowner ) ) AS acl",
                    "        FROM pg_catalog.pg_namespace n",
                    "        WHERE n.nspname !~ '^pg_'",
                    "            AND n.nspname <> 'information_schema'",
                    "),",
                    "classes AS ( ",
                    "    SELECT schemas.schema_oid,",
                    "            schemas.schema_name AS object_schema,",
                    "            c.oid,",
                    "            c.relname::text AS object_name,",
                    "            c.relowner AS owner_oid,",
                    "            CASE",
                    "                WHEN c.relkind = 'r' THEN 'table'",
                    "                WHEN c.relkind = 'v' THEN 'view'",
                    "                WHEN c.relkind = 'm' THEN 'materialized view'",
                    "                WHEN c.relkind = 'c' THEN 'type'",
                    "                WHEN c.relkind = 'i' THEN 'index'",
                    "                WHEN c.relkind = 'S' THEN 'sequence'",
                    "                WHEN c.relkind = 's' THEN 'special'",
                    "                WHEN c.relkind = 't' THEN 'TOAST table'",
                    "                WHEN c.relkind = 'f' THEN 'foreign table'",
                    "                WHEN c.relkind = 'p' THEN 'partitioned table'",
                    "                WHEN c.relkind = 'I' THEN 'partitioned index'",
                    "                ELSE c.relkind::text",
                    "                END AS object_type,",
                    "            CASE",
                    "                WHEN c.relkind = 'S' THEN coalesce ( c.relacl, acldefault ( 's'::\"char\", c.relowner ) )",
                    "                ELSE coalesce ( c.relacl, acldefault ( 'r'::\"char\", c.relowner ) )",
                    "                END AS acl",
                    "        FROM pg_class c",
                    "        JOIN schemas",
                    "            ON ( schemas.schema_oid = c.relnamespace )",
                    "        WHERE c.relkind IN ( 'r', 'v', 'm', 'S', 'f', 'p' )",
                    "),",
                    "cols AS ( ",
                    "    SELECT c.object_schema,",
                    "            null::integer AS oid,",
                    "            c.object_name || '.' || a.attname::text AS object_name,",
                    "            'column' AS object_type,",
                    "            c.owner_oid,",
                    "            coalesce ( a.attacl, acldefault ( 'c'::\"char\", c.owner_oid ) ) AS acl",
                    "        FROM pg_attribute a",
                    "        JOIN classes c",
                    "            ON ( a.attrelid = c.oid )",
                    "        WHERE a.attnum > 0",
                    "            AND NOT a.attisdropped",
                    "),",
                    "procs AS (",
                    "    SELECT schemas.schema_oid,",
                    "            schemas.schema_name AS object_schema,",
                    "            p.oid,",
                    "            p.proname::text AS object_name,",
                    "            p.proowner AS owner_oid,",
                    "            CASE p.prokind",
                    "                WHEN 'a' THEN 'aggregate'",
                    "                WHEN 'w' THEN 'window'",
                    "                WHEN 'p' THEN 'procedure'",
                    "                ELSE 'function'",
                    "                END AS object_type,",
                    "            pg_catalog.pg_get_function_arguments ( p.oid ) AS calling_arguments,",
                    "            coalesce ( p.proacl, acldefault ( 'f'::\"char\", p.proowner ) ) AS acl",
                    "        FROM pg_proc p",
                    "        JOIN schemas",
                    "            ON ( schemas.schema_oid = p.pronamespace )",
                    "),",
                    "udts AS (",
                    "    SELECT schemas.schema_oid,",
                    "            schemas.schema_name AS object_schema,",
                    "            t.oid,",
                    "            t.typname::text AS object_name,",
                    "            t.typowner AS owner_oid,",
                    "            CASE t.typtype",
                    "                WHEN 'b' THEN 'base type'",
                    "                WHEN 'c' THEN 'composite type'",
                    "                WHEN 'd' THEN 'domain'",
                    "                WHEN 'e' THEN 'enum type'",
                    "                WHEN 't' THEN 'pseudo-type'",
                    "                WHEN 'r' THEN 'range type'",
                    "                WHEN 'm' THEN 'multirange'",
                    "                ELSE t.typtype::text",
                    "                END AS object_type,",
                    "            coalesce ( t.typacl, acldefault ( 'T'::\"char\", t.typowner ) ) AS acl",
                    "        FROM pg_type t",
                    "        JOIN schemas",
                    "            ON ( schemas.schema_oid = t.typnamespace )",
                    "        WHERE ( t.typrelid = 0",
                    "                OR ( SELECT c.relkind = 'c'",
                    "                        FROM pg_catalog.pg_class c",
                    "                        WHERE c.oid = t.typrelid ) )",
                    "            AND NOT EXISTS (",
                    "                SELECT 1",
                    "                    FROM pg_catalog.pg_type el",
                    "                    WHERE el.oid = t.typelem",
                    "                        AND el.typarray = t.oid )",
                    "),",
                    "fdws AS (",
                    "    SELECT null::oid AS schema_oid,",
                    "            null::text AS object_schema,",
                    "            p.oid,",
                    "            p.fdwname::text AS object_name,",
                    "            p.fdwowner AS owner_oid,",
                    "            'foreign data wrapper' AS object_type,",
                    "            coalesce ( p.fdwacl, acldefault ( 'F'::\"char\", p.fdwowner ) ) AS acl",
                    "        FROM pg_foreign_data_wrapper p",
                    "),",
                    "fsrvs AS (",
                    "    SELECT null::oid AS schema_oid,",
                    "            null::text AS object_schema,",
                    "            p.oid,",
                    "            p.srvname::text AS object_name,",
                    "            p.srvowner AS owner_oid,",
                    "            'foreign server' AS object_type,",
                    "            coalesce ( p.srvacl, acldefault ( 'S'::\"char\", p.srvowner ) ) AS acl",
                    "        FROM pg_foreign_server p",
                    "),",
                    "all_objects AS (",
                    "    SELECT schema_name AS object_schema,",
                    "            object_type,",
                    "            schema_name AS object_name,",
                    "            null::text AS calling_arguments,",
                    "            owner_oid,",
                    "            acl",
                    "        FROM schemas",
                    "    UNION",
                    "    SELECT object_schema,",
                    "            object_type,",
                    "            object_name,",
                    "            null::text AS calling_arguments,",
                    "            owner_oid,",
                    "            acl",
                    "        FROM classes",
                    "    UNION",
                    "    SELECT object_schema,",
                    "            object_type,",
                    "            object_name,",
                    "            null::text AS calling_arguments,",
                    "            owner_oid,",
                    "            acl",
                    "        FROM cols",
                    "    UNION",
                    "    SELECT object_schema,",
                    "            object_type,",
                    "            object_name,",
                    "            calling_arguments,",
                    "            owner_oid,",
                    "            acl",
                    "        FROM procs",
                    "    UNION",
                    "    SELECT object_schema,",
                    "            object_type,",
                    "            object_name,",
                    "            null::text AS calling_arguments,",
                    "            owner_oid,",
                    "            acl",
                    "        FROM udts",
                    "    UNION",
                    "    SELECT object_schema,",
                    "            object_type,",
                    "            object_name,",
                    "            null::text AS calling_arguments,",
                    "            owner_oid,",
                    "            acl",
                    "        FROM fdws",
                    "    UNION",
                    "    SELECT object_schema,",
                    "            object_type,",
                    "            object_name,",
                    "            null::text AS calling_arguments,",
                    "            owner_oid,",
                    "            acl",
                    "        FROM fsrvs",
                    "),",
                    "acl_base AS (",
                    "    SELECT object_schema,",
                    "            object_type,",
                    "            object_name,",
                    "            calling_arguments,",
                    "            owner_oid,",
                    "            ( aclexplode ( acl ) ).grantor AS grantor_oid,",
                    "            ( aclexplode ( acl ) ).grantee AS grantee_oid,",
                    "            ( aclexplode ( acl ) ).privilege_type AS privilege_type,",
                    "            ( aclexplode ( acl ) ).is_grantable AS is_grantable",
                    "        FROM all_objects",
                    ")"
                ]
            )

            if category == "role-grants":
                return " ".join(
                    [
                        in_str,
                        "SELECT ",
                        "        acl_base.object_type as \"Type\",",
                        "        acl_base.object_schema as \"Schema\","
                        "        acl_base.object_name as \"Object\",",
                        "        acl_base.calling_arguments as \"Arguments\", ",
                        "        owner.role_name AS \"Owner\", ",
                        "        acl_base.privilege_type as \"Privilege\",",
                        "        grantor.role_name AS \"Granted By\",",
                        "        acl_base.is_grantable as \"With Grant\"",
                        "    FROM acl_base",
                        "    JOIN rol owner",
                        "        ON ( owner.oid = acl_base.owner_oid )",
                        "    JOIN rol grantor",
                        "        ON ( grantor.oid = acl_base.grantor_oid )",
                        "    JOIN rol grantee",
                        "        ON ( grantee.oid = acl_base.grantee_oid )",
                        "    WHERE grantee.role_name = %s ",
                        "order by acl_base.object_type, acl_base.object_schema, acl_base.object_name, acl_base.privilege_type"
                    ]
                )
            
            if category == "grants":
                return " ".join(
                    [
                        in_str,
                        "SELECT /*acl_base.object_schema,",
                        "        acl_base.object_type,",
                        "        acl_base.object_name,",
                        "        acl_base.calling_arguments, ",
                        "        owner.role_name AS object_owner, */",
                        "        grantee.role_name AS \"Role\",",
                        "        acl_base.privilege_type as \"Privilege\",",
                        "        grantor.role_name AS \"Granted By\",",
                        "        acl_base.is_grantable as \"With Grant\"",
                        "    FROM acl_base",
                        "    JOIN rol owner",
                        "        ON ( owner.oid = acl_base.owner_oid )",
                        "    JOIN rol grantor",
                        "        ON ( grantor.oid = acl_base.grantor_oid )",
                        "    JOIN rol grantee",
                        "        ON ( grantee.oid = acl_base.grantee_oid )",
                        "    WHERE case when acl_base.object_type = 'partitioned table' then 'table' else acl_base.object_type end = %s ",
                        "        and acl_base.object_schema = %s ",
                        "        and CASE ",
                        "            WHEN acl_base.object_type in ('function', 'procedure') then ",
                        "                CONCAT(acl_base.object_name, '(', COALESCE(acl_base.calling_arguments,''), ')')",
                        "            else ",
                        "                acl_base.object_name ",
                        "            end = %s",
                        "order by acl_base.object_type, grantee.role_name, acl_base.privilege_type"
                    ]
                )
        
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
                data["meta"].append({
                    "name": "Name",
                    "value": record[1],
                })

                data["meta"].append({
                    "name": "Owner",
                    "value": record[2],
                })

                data["sections"]["Source"]["data"] = record[0]

            sql = self._sql("grants")
            params = ["schema", record[1], record[1]]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

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
                    "Permissions": { "type": "table", "headers": [], "records": [] },
                    "Source": { "type": "code", "data": "" }
                }
            }

            sql = self._sql("table-detail")
            params = [path["schema"], target]

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

                data["meta"].append({
                    "name": "RLS Enabled",
                    "value": record[4],
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
                    "name": "Tablespace",
                    "value": record[4],
                })

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
                    "name": "Last Value",
                    "value": record[4],
                })

                data["meta"].append({
                    "name": "Data Type",
                    "value": record[5],
                })

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

            sql = self._sql("role-grants")
            params = [target]
            for headers, record in self.fetchmany(sql, params, 1000):
                data["sections"]["Permissions"]["headers"] = headers
                data["sections"]["Permissions"]["records"].append(record)

        return data
        