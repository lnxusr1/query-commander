import os
import json
import yaml
import logging

from core.connections import Connections

class Settings:
    CONFIG_PATH = os.environ.get("QRYCOMM_CONFIG_PATH", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "config")))

    def __init__(self):
        self.data = {}

        with open(os.path.join(self.CONFIG_PATH, "settings.yml"), "r", encoding="UTF-8") as fp:
            self.data = yaml.safe_load(fp)

        self._connections = Connections(global_settings=self, **self.data.get("connections", {}))

    def sys_connections(self, conn_name=None):
        if conn_name is None:
            return self._connections.list()
        else:
            return self._connections.get(conn_name)
    
    @property
    def sys_authenticator(self):
        return self.data.get("authenticator", { "type": "local" })
    
    @property
    def sys_tokenizer(self):
        return self.data.get("tokenizer", { "type": "local" })
    
    @property
    def sys_profiler(self):
        return self.data.get("profiler", { "type": "local" })

    @property
    def sys_mappings(self):
        return self.data.get("mappings", {})
    
    @property
    def records_per_request(self):
        return int(self.data.get("settings", {}).get("records_per_request", 200))
    
    def sys_settings(self, name, default=None):
        return self.data.get("settings", {}).get(name, default)

    def aws_region_name(self, in_settings):
        return in_settings.get("aws_region_name", self.sys_settings("aws_region_name"))

    def aws_credentials(self, in_settings):
        if not isinstance(in_settings, dict):
            in_settings = {}

        if in_settings.get("aws_profile_name") is not None:
            return { 
                "profile_name": in_settings.get("aws_profile_name")
            }

        if in_settings.get("aws_access_key") is not None:
            return { 
                "aws_access_key_id": in_settings.get("aws_access_key"), 
                "aws_secret_access_key": in_settings.get("aws_secret_key")
            }

        if self.sys_settings("aws_profile_name") is not None:
            return { 
                "profile_name": self.sys_settings("aws_profile_name")
            }

        if self.sys_settings("aws_access_key") is not None:
            return { 
                "aws_access_key_id": self.sys_settings("aws_access_key"), 
                "aws_secret_access_key": self.sys_settings("aws_secret_key")
            }

        return {}

def load_settings():
    s = Settings()
    return s

settings = load_settings()
