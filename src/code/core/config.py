import os
import yaml


class Settings:
    CONFIG_PATH = os.environ.get("DBSQL_PATH", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "config")))

    def __init__(self):
        self.data = {}
        with open(os.path.join(self.CONFIG_PATH, "settings.yml"), "r", encoding="UTF-8") as fp:
            self.data = yaml.safe_load(fp)

    @property
    def sys_connections(self):
        return self.data.get("connections", {})
    
    @property
    def sys_authenticator(self):
        return self.data.get("authenticator", { "type": "config" })
    
    @property
    def sys_tokenizer(self):
        return self.data.get("tokenizer", { "type": "local" })
    
    @property
    def sys_mappings(self):
        return self.data.get("mappings", {})
        

def load_settings():
    s = Settings()
    return s

settings = load_settings()
