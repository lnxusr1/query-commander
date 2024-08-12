import os
import datetime
import tempfile
import hashlib
import json
import logging
import http.cookies
from core.helpers import get_utc_now, generate_session_token, validate_string
from core.config import settings as cfg
from core.profiler import profiler as prf

class Tokens:
    def __init__(self, **kwargs):
        self.token = None
        self.data = None
        self._is_loaded = False
        self.safe_password = str(kwargs.get("safe_password", "default_password"))
        self.remote_addr = ""
        self.timeout = int(kwargs.get("timeout", 20))
        self._connections = None

    def _get_token_data(self):
        # OVERRIDE THIS METHOD

        return { 
            "type": "token",
            "expires": get_utc_now().strftime('%a, %d-%b-%Y %H:%M:%S UTC'), 
            "connections": [], 
            "username": None, 
            "credentials": None,
            "roles": [],
            "connections": [],
            "role_selected": ""
        }

    def _put_token_data(self):
        # OVERRIDE THIS METHOD

        return False

    def _remove_token_data(self):
        # OVERRIDE THIS METHOD

        return False

    def is_expired(self, timestamp):
        if self.token is None or self.data is None:
            return True
        
        c_ts = get_utc_now()
        d_ts = datetime.datetime.strptime(timestamp, '%a, %d-%b-%Y %H:%M:%S UTC')

        if c_ts <= d_ts:
            return False
            
        return True

    def _get(self):
        if self.token is not None and self.data is not None:
            return True

        data = None
        if self.token is not None and self.data is None:
            data = self._get_token_data()
            self._is_loaded = True
        
        if self.token is None and self.data is None:
            self.token = generate_session_token()

        if isinstance(data, dict):
            self.data = data
        else:
            self.data = {
                "type": "token",
                "expires": get_utc_now().strftime('%a, %d-%b-%Y %H:%M:%S UTC'), 
                "connections": [], 
                "username": None, 
                "credentials": None,
                "roles": [],
                "connections": [],
                "role_selected": ""
            }

        return True

    def validate(self):
        self._get()

        if str(self.data.get("type", "")) == "token" and self.data.get("expires") is not None:
            if not self.is_expired(self.data.get("expires")):
                return self.update()

        self._remove_token_data()
        return False
    
    def validate_connection(self, connection_data):
        if not isinstance(connection_data, dict):
            return False
        
        for r in self.roles:
            if r in connection_data.get("roles", []):
                return True
            
        return False
    
    def update(self):
        self._get()
        
        expiration_time = get_utc_now() + datetime.timedelta(minutes=int(self.timeout))
        self.set("expires", expiration_time.strftime('%a, %d-%b-%Y %H:%M:%S UTC'))
        self.set("token", self.token)
       
        self._is_loaded = True
        return self._put_token_data()
    
    def remove(self):
        self._get()
        return self._remove_token_data()
        
    def set_token(self, token=None):
        if token is not None:
            token = str(token).strip()
            if not validate_string(token, max_length=100):
                raise ValueError("Invalid token format")

        self.token = token
    
    def set_remote_addr(self, value):
        self.remote_addr = str(value)[0:256]

    def set(self, name, value):
        self._get()
        if (name == "username"):
            self.data[name] = str(value)[0:100]
        else:
            self.data[name] = value

        return True

    def purge(self):    
        return False
    
    @property
    def username(self):
        self._get()
        return self.data.get("username")
    
    @property
    def credentials(self):
        self._get()
        return self.data.get("credentials")
    
    @property
    def roles(self):
        self._get()
        return self.data.get("roles", [])

    @property
    def role_selected(self):
        self._get()
        return self.data.get("role_selected", None)

    def connections(self):
        if self._connections is not None:
            return self._connections
        
        if len(self.data.get("connections", [])) > 0:
            return self.data.get("connections", [])
        
        if cfg.sys_authenticator.get("type", "local") == "local":
            self._connections = [{ "name": str(x), "type": cfg.sys_connections(x).get("type") } for x in cfg.sys_connections()]
            return self._connections
        else:
            self._get()
            if True:
#            if self.role_selected != "":
#                if self.role_selected not in self.roles:
#                    return []

                conns = []
                for x in cfg.sys_connections():
#                    if self.role_selected in cfg.sys_connections.get(x).get("roles"):
#                        conns.append({ "name": str(x), "type": cfg.sys_connections.get(x).get("type")})
                    for r in self.roles:
                        if r in cfg.sys_connections(x).get("roles"):
                            conns.append({ "name": str(x), "type": cfg.sys_connections(x).get("type")})
                            break

                self._connections = conns
                return self._connections
            else:
                return []

    @property
    def cookie(self):
        ret = None

        if self._is_loaded and self.token is not None and self.data is not None:
            cookie = http.cookies.SimpleCookie()
            cookie['token'] = self.token
            
            #if self.is_expired(self.data.get("expires")):
            #    expiration_time = get_utc_now() - datetime.timedelta(days=365) # 1 year ago
            #else:
            #    expiration_time = get_utc_now() + datetime.timedelta(days=3650) # 10 years
            
            expiration_time = datetime.datetime.strptime(self.data.get("expires"), '%a, %d-%b-%Y %H:%M:%S UTC')
            cookie['token']['expires'] = expiration_time.strftime('%a, %d-%b-%Y %H:%M:%S UTC')
            cookie['token']['secure'] = True
            ret = cookie.output()

        return ret
    
    def get_profiler(self):
        prf.set_username(self.username)
        return prf

class LocalTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.path = kwargs.get("path", os.path.join(tempfile.gettempdir(), "tokens"))

    def _get_token_data(self):
        if self.token is None:
            return super()._get_token_data()
        
        data = None

        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self.token.encode()).hexdigest()}.json")
            if os.path.exists(filename):
                with open(filename, "r", encoding="UTF-8") as fp:
                    data = json.load(fp)
        except:
            return super()._get_token_data()

        return data

    def _put_token_data(self):
        if self.token is None or self.data is None:
            return False
        
        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self.token.encode()).hexdigest()}.json")
            os.makedirs(self.path, exist_ok=True)

            with open(filename, "w", encoding="UTF-8") as fp:
                json.dump(self.data, fp)
        except:
            return False
        
        return True

    def _remove_token_data(self):
        if self.token is None or self.data is None:
            return False
        
        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self.token.encode()).hexdigest()}.json")
            if os.path.exists(filename):
                os.remove(filename)

        except:
            return False

        return True
    
    def purge(self):
        if os.path.exists(self.path):
            file_list = os.listdir(self.path)
            for file_name in file_list:
                if file_name.endswith(".json"):
                    with open(os.path.join(self.path, file_name), "r", encoding="UTF-8") as fp:
                        data = json.load(fp)
                    
                    if self.is_expired(data.get("expires")):
                        username = data.get("username")
                        file_name_base = file_name.rsplit('.', 1)[0]
                        logging.info(f"[{username}] Expired token purged. - {file_name_base}")
                        os.remove(os.path.join(self.path, file_name))
        
        return True


class RedisTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port", 6379)

        import redis
        self.conn = redis.Redis(
            host=self.host,
            port=self.port,
            ssl=kwargs.get("options", {}).get("ssl", False),
            ssl_cert_reqs="none",
            decode_responses=True
        )

    def _get_token_data(self):
        if self.token is None:
            return super()._get_token_data()
        
        data = None

        try:
            d = self.conn.get(self.token)
            data = json.loads(d if isinstance(d, str) else "{}")
            self.token = self.token

        except:
            return super()._get_token_data()

        return data

    def _put_token_data(self):
        if self.token is None or self.data is None:
            return False
        
        try:
            self.conn.set(self.token, json.dumps(self.data))
        except:
            return False
        
        return True

    def _remove_token_data(self):
        if self.token is None:
            return False
        
        try:
            self.conn.delete(self.token)
        except:
            return False

        return True 
    
    def purge(self):
        cursor = 0
        while True:
            cursor, tokens = self.conn.scan(cursor=cursor)
            for token in tokens:
                data = json.loads(self.conn.get(token))
                if data.get("type", "") == "token":
                    if self.is_expired(data.get("expires")):
                        username = data.get("username")
                        try:
                            self.conn.delete(token)
                            logging.info(f"[{username}] Expired token purged. - {token}")
                        except:
                            logging.error(f"[{username}] Unable to remove expired token - {token}")

            if cursor == 0:
                break

        return True


class DynamoDBTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        import boto3
        boto3.set_stream_logger('boto3', logging.WARNING)
        boto3.set_stream_logger('botocore', logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        self.table_name = kwargs.get("table", "tokens")

        session = boto3.Session(**cfg.aws_credentials(kwargs))
        self.conn = session.client('dynamodb', region_name=cfg.aws_region_name(kwargs))

    def _get_token_data(self):
        if self.token is None:
            return super()._get_token_data()
        
        data = super()._get_token_data()

        try:
            response = self.conn.get_item(TableName=self.table_name, Key={ "token": { "S": str(self.token) } })
            d = response["Item"].get("data").get("S")
            data = json.loads(d if isinstance(d, str) else "{}")
        except:
            return super()._get_token_data()

        return data

    def _put_token_data(self):
        if self.token is None or self.data is None:
            return False
        
        try:
            self.conn.put_item(TableName=self.table_name, Item={ "token": { 'S': self.token}, "data": {'S': json.dumps(self.data) }})
        except:
            return False
        
        return True

    def _remove_token_data(self):
        if self.token is None:
            return False

        try:
            self.conn.delete_item(TableName=self.table_name, Key={ "token": { "S": self.token } })
        except:
            return False
        
        return True
    
    def purge(self):
        try:
            response = self.conn.scan(TableName=self.table_name)
            for item in response["Items"]:
                data = json.loads(item.get("data").get("S"))
                if data.get("type", "") == "token":
                    if self.is_expired(data.get("expires")):
                        username = data.get("username")
                        token = item.get("token")
                        
                        try:
                            self.conn.delete_item(TableName=self.table_name, Key={ "token": token })
                            logging.info(f"[{username}] Expired token purged. - {token}")
                        except:
                            logging.error(f"[{username}] Unable to remove expired token - {token}")
        except:
            pass
        
        return True


def get_tokenizer(connection_details):
    if connection_details.get("type", "local") == "local":
        return LocalTokens(**connection_details)
    
    if connection_details.get("type", "local") == "redis":
        return RedisTokens(**connection_details)
    
    if connection_details.get("type", "local") == "dynamodb":
        return DynamoDBTokens(**connection_details)
    
    return Tokens(**connection_details)


tokenizer = get_tokenizer(cfg.sys_tokenizer)
