import os
import json
import logging

class Connections:
    def __init__(self, global_settings=None, **kwargs):
        self.settings = kwargs
        self._connections = None
        self.session = None
        self.client = None
        self.global_settings = global_settings

    def _get_client(self):
        import boto3

        if self.session is None:
            self.session = boto3.session.Session(**self.global_settings.aws_credentials(self.settings))

        if self.client is None:
            self.client = self.session.client(
                service_name='secretsmanager',
                region_name=self.global_settings.aws_region_name(self.settings)
            )

        return self.client

    def _load_config(self):
        src_conns = self.settings.get("items", [])
        conns = {}
        if src_conns is not None:
            if isinstance(src_conns, list):
                for conn in src_conns:
                    if isinstance(conn, dict):
                        c_name = conn.get("name", conn.get("host"))
                        if c_name is not None:
                            conns[c_name] = conn
        
        return conns

    def _load_secretsmanager(self):
        client = self._get_client()

        conns = {}
        response = client.list_secrets(IncludePlannedDeletion=False, Filters=self.settings.get("filters", []))
        for secret in response['SecretList']:
            conns[secret.get("Name")] = None
                
        return conns

    def load(self):
        if self._connections is not None:
            return
        
        c_type = os.environ.get("CONNECTIONS_TYPE", self.settings.get("type", "config"))
        if c_type == "config":
            self._connections = self._load_config()

        if c_type in ["secretsmanager", "secretmanager"]:
            self._connections = self._load_secretsmanager()

    def list(self):
        self.load()
        return self._connections
    
    def _get_secretsmanager(self, conn_name):
        if self._connections is not None and self._connections.get(conn_name) is not None:
            return self._connections.get(conn_name)

        client = self._get_client()

        sv = client.get_secret_value(
            SecretId=conn_name
        )
        
        svd = json.loads(sv['SecretString'])

        if self._connections is None:
            self._connections = {}
        
        self._connections[conn_name] = svd
        return self._connections.get(conn_name)

    def get(self, conn_name):

        c_type = os.environ.get("CONNECTIONS_TYPE", self.settings.get("type", "config"))
        if c_type == "config":
            self.load() # if not already loaded
            return self._connections.get(conn_name)

        if c_type in ["secretsmanager", "secretmanager"]:
            return self._get_secretsmanager(conn_name)
            
