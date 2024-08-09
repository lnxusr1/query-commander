import os
import json
import yaml
import logging


class Settings:
    CONFIG_PATH = os.environ.get("QRYCOMM_CONFIG_PATH", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "config")))

    def __init__(self):
        self.data = {}
        self._connections = None
        with open(os.path.join(self.CONFIG_PATH, "settings.yml"), "r", encoding="UTF-8") as fp:
            self.data = yaml.safe_load(fp)

    @property
    def sys_connections(self):
        if self._connections is None:
            if self.data.get("connections", {}).get("type", "local") == "local":
                src_conns = self.data.get("connections", {}).get("items")
                conns = {}
                if src_conns is not None:
                    if isinstance(src_conns, list):
                        for conn in src_conns:
                            if isinstance(conn, dict):
                                c_name = conn.get("name", conn.get("host"))
                                if c_name is not None:
                                    conns[c_name] = conn
                
                self._connections = conns

            if self.data.get("connections", {}).get("type", "local") in ["secretsmanager", "secretmanager"]:
                import boto3
                from botocore.exceptions import ClientError

                session = boto3.session.Session(**self.aws_credentials(self.data.get("connections", {})))
                client = session.client(
                    service_name='secretsmanager',
                    region_name=self.aws_region_name(self.data.get("connections", {}))
                )

                prefix_text = self.data.get("connections", {}).get("prefix")

                conns = {}
                response = client.list_secrets()
                for secret in response['SecretList']:
                    if prefix_text is None:
                        sv = client.get_secret_value(
                            SecretId=secret.get("Name")
                        )
                        
                        svd = json.loads(sv['SecretString'])
                        conns[svd.get("name")] = svd
                    else:
                        if str(secret.get("Name")).startswith(str(prefix_text)):
                            sv = client.get_secret_value(
                                SecretId=secret.get("Name")
                            )
                            
                            svd = json.loads(sv['SecretString'])
                            conns[svd.get("name")] = svd
                        
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
