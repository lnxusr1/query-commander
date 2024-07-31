import os
import yaml


class Settings:
    CONFIG_PATH = os.environ.get("DBSQL_PATH", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "config")))

    def __init__(self):
        self.data = {}
        self._connections = None
        with open(os.path.join(self.CONFIG_PATH, "settings.yml"), "r", encoding="UTF-8") as fp:
            self.data = yaml.safe_load(fp)

    @property
    def sys_connections(self):
        if self._connections is None:
            #TODO: Allow getting connections from secret manager as a list

            src_conns = self.data.get("connections")
            conns = {}
            if src_conns is not None:
                if isinstance(src_conns, list):
                    for conn in src_conns:
                        if isinstance(conn, dict):
                            c_name = conn.get("name", conn.get("host"))
                            if c_name is not None:
                                conns[c_name] = conn
            
            self._connections = conns

        return self._connections
    
    @property
    def sys_authenticator(self):
        return self.data.get("authenticator", { "type": "config" })
    
    @property
    def sys_tokenizer(self):
        return self.data.get("tokenizer", { "type": "local" })
    
    @property
    def sys_mappings(self):
        return self.data.get("mappings", {})
    
    @property
    def records_per_request(self):
        return int(self.data.get("settings", {}).get("records_per_request", 200))
        

def load_settings():
    s = Settings()
    return s

settings = load_settings()
