import os
import datetime
import tempfile
import hashlib
import json
import logging
import http.cookies
from core.helpers import get_utc_now, generate_session_token, validate_string
from core.config import settings as cfg


class Tokens:
    def __init__(self, **kwargs):
        self.token = None
        self.data = None
        self._is_loaded = False
        self.safe_password = str(cfg.sys_tokenizer.get("safe_password", "default_password"))
        self.remote_addr = ""

    def _get_token_data(self):
        # OVERRIDE THIS METHOD

        return { 
            "type": "token",
            "expires": get_utc_now(), 
            "connections": [], 
            "username": None, 
            "credentials": None 
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
                return True

        self._remove_token_data()
        return False
    
    def update(self):
        self._get()
        
        expiration_time = get_utc_now() + datetime.timedelta(minutes=int(cfg.sys_tokenizer.get("timeout", 20)))
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

    @property
    def connections(self):
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


class LocalTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.path = cfg.sys_tokenizer.get("path", os.path.join(tempfile.gettempdir(), "tokens"))

    def _get_token_data(self):
        if self.token is None:
            return False
        
        data = None

        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self.token.encode()).hexdigest()}.json")
            if os.path.exists(filename):
                with open(filename, "r", encoding="UTF-8") as fp:
                    data = json.load(fp)
        except:
            return None

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

    @property
    def connections(self):
        self._get()
        if self.role_selected != "":
            return [str(x) for x in cfg.sys_connections]
        else:
            return []


class RedisTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _get_token_data(self):
        # OVERRIDE THIS METHOD

        return None

    def _put_token_data(self):
        # OVERRIDE THIS METHOD

        return False

    def _remove_token_data(self):
        # OVERRIDE THIS METHOD

        return False 
    
    def purge(self):
        return False

    @property
    def connections(self):
        # OVERRIDE THIS METHOD
        self._get()
        return []


class DynamoDBTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _get_token_data(self):
        # OVERRIDE THIS METHOD

        return None

    def _put_token_data(self):
        # OVERRIDE THIS METHOD

        return False

    def _remove_token_data(self):
        # OVERRIDE THIS METHOD

        return False 
    
    def purge(self):
        return False

    @property
    def connections(self):
        # OVERRIDE THIS METHOD
        self._get()
        return []


def get_tokenizer(connection_details, db_connections):
    if connection_details.get("type", "local") == "local":
        return LocalTokens(db_conns=db_connections, **connection_details.get("connection", {}))
    
    if connection_details.get("type", "local") == "redis":
        return RedisTokens(db_conns=db_connections, **connection_details.get("connection", {}))
    
    if connection_details.get("type", "local") == "dynamodb":
        return DynamoDBTokens(db_conns=db_connections, **connection_details.get("connection", {}))
    
    return Tokens(db_conns=db_connections, **connection_details["connection"])


tokenizer = get_tokenizer(cfg.sys_tokenizer, cfg.sys_connections)
