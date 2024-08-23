import os
import json
import yaml
import logging

from querycommander.core.connections import Connections

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
    def profiles(self):
        p = self.data.get("settings", {}).get("profiles", "enable")
        if str(p).lower() in ["enable", "enabled", ""]:
            return True
        
        return False
    
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
    
    @property
    def rate_limit_records(self):
        return int(self.data.get("settings", {}).get("rate_limit", {}).get("records", -1))

    @property
    def rate_limit_period(self):
        return int(self.data.get("settings", {}).get("rate_limit", {}).get("period", -1))
    
    @property
    def cdn_fontawesome(self):
        far = self.data.get("settings", {}).get("cdns", {}).get("fontawesome", {})
        fa = {
            "href": far.get("url", "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"),
            "integrity": far.get("integrity", "sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA=="),
            "crossorigin": far.get("crossorigin", "anonymous"),
            "referrerpolicy": far.get("referrerpolicy", "no-referrer")
        }
        return f"<link rel=\"stylesheet\" " + " ".join([f"{x}=\"{fa[x]}\"" for x in fa]) + " />"

    @property
    def cdn_jquery(self):
        far = self.data.get("settings", {}).get("cdns", {}).get("jquery", {})
        fa = {
            "src": far.get("url", "https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js")
        }
        return f"<script " + " ".join([f"{x}=\"{fa[x]}\"" for x in fa]) + "></script>"

    @property
    def log_level(self):
        lvl = str(self.data.get("settings", {}).get("log_level", "info")).lower()

        if lvl == "critical":
            return logging.CRITICAL

        if lvl == "error":
            return logging.ERROR

        if lvl == "warning":
            return logging.WARNING

        if lvl == "debug":
            return logging.DEBUG
        
        return logging.INFO

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
