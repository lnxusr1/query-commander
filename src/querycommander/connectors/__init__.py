import os
import logging
import traceback
from querycommander.core.config import settings as cfg

class Connector:
    def __init__(self, **kwargs):
        self.tokenizer = kwargs.get("tokenizer")
        self._type = kwargs.get("type")
        self.connection = None
        self.err = []
        self.columns = []
        self.logger = logging.getLogger("CONNECTION")
        self.logger.setLevel(cfg.log_level)

        self.database = kwargs.get("database")
        self.schema = kwargs.get("schema")

    @property
    def explain_as_output(self):
        return False

    @property
    def exec_time(self):
        """ Execution time in seconds """
        return None
    
    @property
    def notices(self):
        return []

    def open(self):
        self.err.append("Not implemented.")
        return False

    def close(self):
        self.err.append("Not implemented.")
        return False

    def rollback(self):
        self.err.append("Not implemented.")
        return False

    def commit(self):
        self.err.append("Not implemented.")
        return False

    def execute(self, sql, params):
        self.err.append("Not implemented.")
        return None

    def fetchmany(self, sql, params, size=None, query_type=None):
        self.err.append("Not implemented.")
        return
    
    def meta(self, type, target, path):
        self.err.append("Not implemented.")

        # Return TYPE and RECORD DATA
        return None, None
    
    def ddl(self, type, target, path):
        self.err.append("Not implemented.")
        return None

    def details(self, type, target, path):
        self.err.append("Not implemented.")
        return None

    def get_sql_file(self, category):
        if self._type is not None:
            file_path = os.path.join(os.path.dirname(__file__), "extra_sql", str(self._type).lower())

            try:
                files = os.listdir(file_path)
                file_name = files[files.index(category.lower().strip().replace('-','_') + ".sql")]
                file_name = os.path.join(file_path, file_name)
                if os.path.exists(file_name):
                    with open(file_name, "r", encoding="UTF-8") as fp:
                        contents = fp.read().rstrip()
                    
                    return contents
            except:
                pass

        return None
    
    def log(self, content, message=None, with_trace=False):
        if with_trace:
            self.logger.debug(str(traceback.format_exc()))

        self.logger.error(f"[{self.tokenizer.username}@{self.tokenizer.remote_addr}] - {self.host} - {str(content)} - {self.tokenizer.token}")

        if message is None:
            message = content
        self.err.append(str(message))

        return True