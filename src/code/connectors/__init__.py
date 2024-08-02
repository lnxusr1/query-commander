class Connector:
    def __init__(self, **kwargs):
        self._type = kwargs.get("type")
        self.connection = None
        self.err = []
        self.columns = []

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

    def fetchmany(self, sql, params):
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
