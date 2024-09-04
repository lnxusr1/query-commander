import os
import sys
import datetime
import tempfile
import hashlib
import json
import traceback
import logging
import http.cookies
from querycommander.core.helpers import get_utc_now, generate_session_token, validate_string
from querycommander.core.config import settings as cfg
from querycommander.core.profiler import get_profiler

class Tokens:
    def __init__(self, **kwargs):
        self.token = None
        self.data = None
        self._is_loaded = False
        self.safe_password = str(os.environ.get('TOKENIZER_SAFE_PASSWORD', kwargs.get("safe_password", "default_password")))
        self.remote_addr = ""
        self.timeout = int(os.environ.get('TOKENIZER_TIMEOUT', kwargs.get("timeout", 20)))
        self._connections = None
        self._username = None
        self._do_update = False
        self.logger = logging.getLogger("TOKENIZER")
        self.logger.setLevel(cfg.log_level)

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

    #def _remove_token_data(self):
    #    # OVERRIDE THIS METHOD
    #
    #    return False

    def is_expired(self, timestamp):
        if self.token is None or self.data is None:
            return True
        
        c_ts = get_utc_now()
        d_ts = datetime.datetime.strptime(timestamp, '%a, %d-%b-%Y %H:%M:%S UTC')

        if c_ts <= d_ts:
            return False
            
        return True

    def _get(self):
        if self.token is not None and self._username is not None and self.data is not None:
            return True

        data = None
        if self.token is not None and self._username is not None and self.data is None:
            data = self._get_token_data()
            self._is_loaded = True

        if self.token is None and self.data is None:
            self.token = generate_session_token()

        if isinstance(data, dict):
            if str(data.get("token")) != str(self.token):
                self.data = None
            else:
                self.data = data
        
        if self.data is None:
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
            self._is_loaded = True

        return True

    def validate(self):
        self._get()

        #self.logger.debug(f"{self._username} == {self.token} == {self.data}")

        if self.token is not None \
            and len(str(self.data.get("token", "")).strip()) >= 20 \
            and str(self.data.get("token", "")).strip() == str(self.token):

            if str(self.data.get("type", "")) == "token" and self.data.get("expires") is not None:
                if not self.is_expired(self.data.get("expires")):
                    self._do_update = True
                    return True

        #self._remove_token_data()
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

        self._do_update = False
        if self._username is None or self.token is None:
            self.logger.debug("No username or token, cannot update token")
            return False
    
        expiration_time = get_utc_now() + datetime.timedelta(minutes=int(self.timeout))
        self.set("expires", expiration_time.strftime('%a, %d-%b-%Y %H:%M:%S UTC'))
        self.set("token", self.token)
       
        self._is_loaded = True
        return self._put_token_data()
    
    def remove(self):
        self._get()
        
        self._do_update = False
        if self._username is None or self.token is None:
            self.logger.debug("Username or token is blank, cannnot remove token")
            return False
    
        expiration_time = get_utc_now()
        self.set("expires", expiration_time.strftime('%a, %d-%b-%Y %H:%M:%S UTC'))
        self.set("token", "INVALID")
       
        self._is_loaded = True
        return self._put_token_data()
        
    def set_token(self, token=None):
        if len(str(token).strip()) < 10:
            token = None

        if token is not None:
            token = str(token).strip()
            if not validate_string(token, max_length=100):
                raise ValueError("Invalid token format")

        self.token = token

    def set_username(self, value):
        #self.logger.debug(f"Setting username: {value}")
        if value is None:
            return
        
        if value is not None:
            if not validate_string(value, max_length=256):
                raise ValueError("Invalid username format")
        
        self._username = str(value).lower()
    
    def set_remote_addr(self, value):
        self.remote_addr = str(value)[0:256]

    def set(self, name, value):
        self._get()
        if (name == "username"):
            self.data[name] = str(value)[0:100]
        else:
            self.data[name] = value

        return True

    #def purge(self):    
    #    return False
    
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

    def history(self):
        return self.data.get("history", [])
    
    def get_records_remaining(self):
        if cfg.rate_limit_period <= 0 and cfg.rate_limit_records <= 0:
            return cfg.records_per_request
        
        timestamp = get_utc_now() - datetime.timedelta(minutes=cfg.rate_limit_period)
        history_data = self.history()
        r_count = 0
        i = len(history_data) - 1
        while i >= 0:
            item = history_data[i]
            ts = datetime.datetime.strptime(str(item[0]), "%Y-%m-%d %H:%M:%S")
            if ts > timestamp:
                r_count = r_count + item[1]
            else:
                del history_data[i]

            i = i - 1

        # Put it back for next time
        self.set("history", history_data)

        r_count = cfg.rate_limit_records - r_count
        return r_count if r_count > 0 else 0

    def connections(self):
        if self._connections is not None and isinstance(self._connections, list) and len(self._connections) > 0:
            #self.logger.debug("CONNECTIONS FROM LOCAL CACHE")
            return self._connections
        
        if len(self.data.get("connections", [])) > 0:
            #self.logger.debug("CONNECTIONS FROM LOCAL DATA")
            return self.data.get("connections", [])
        
        if cfg.sys_authenticator.get("type", "local") == "local":
            #self.logger.debug("CONNECTIONS FROM CONFIG")
            self._connections = [{ "name": str(x), "type": str(cfg.sys_connections(x).get("type")).lower() } for x in cfg.sys_connections()]
            return self._connections
        else:
            #self.logger.debug("CONNECTIONS FROM PROCESSING")
            self._get()
            #self.logger.debug(f"{self._connections}")
            conns = []
            for x in cfg.sys_connections():
                for r in self.roles:
                    #self.logger.debug(f"Role {r}")
                    l_conn = cfg.sys_connections(x)
                    conn_roles = [x.lower().strip() for x in l_conn.get("roles", [])]
                    if not isinstance(r, str):
                        self.logger.debug(str(r))
                        
                    if str(r).lower().strip() in conn_roles:
                        #self.logger.debug(f"Role {r} in {conn_roles}")
                        conns.append({ "name": str(x), "type": str(cfg.sys_connections(x).get("type")).lower() })
                        break

            #self.logger.debug(f"{self._connections}")
            self._connections = conns
            return self._connections

    def cookie(self, extend=None, req_type=None):
        ret = None

        if self._is_loaded and self.token is not None and self.data is not None:

            if extend is not None:
                if extend:
                    self.update()
            else:
                if self._do_update:
                    self.update()

            cookie = http.cookies.SimpleCookie()
            
            expiration_time = datetime.datetime.strptime(self.data.get("expires"), '%a, %d-%b-%Y %H:%M:%S UTC')
            
            if self.token is not None and str(self.token) != "None":
                cookie['token'] = self.token
                if str(req_type) == "logout":
                    cookie['token']['expires'] = expiration_time.strftime('%a, %d-%b-%Y %H:%M:%S UTC')

                #cookie['token']['expires'] = 0 # Session cookie
                cookie['token']['secure'] = True
            
            if self._username is not None and str(self._username) != "None":
                cookie['username'] = self._username
                if str(req_type) == "logout":
                    cookie['username']['expires'] = expiration_time.strftime('%a, %d-%b-%Y %H:%M:%S UTC')

                #cookie['username']['expires'] = 0 # Session cookie
                cookie['username']['secure'] = True

            ret = cookie.output()

        return ret
    
    def get_profiler(self):
        prf = get_profiler(cfg.sys_profiler)
        prf.set_username(self.username)  # NOTICE: this is the property and not the key
        return prf

class LocalTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.path = os.environ.get("TOKENIZER_PATH", kwargs.get("path", os.path.join(tempfile.gettempdir(), "tokens")))

    def _get_token_data(self):
        if self.token is None or self._username is None:
            return super()._get_token_data()
        
        data = None

        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self._username.encode()).hexdigest()}.json")
            if os.path.exists(filename):
                with open(filename, "r", encoding="UTF-8") as fp:
                    data = json.load(fp)
        except:
            return super()._get_token_data()

        return data

    def _put_token_data(self):
        if self.token is None or self._username is None or self.data is None:
            self.logger.error(f"[{self._username}@{self.remote_addr}] Unable to place token - {self.token}")
            return False
        
        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self._username.encode()).hexdigest()}.json")
            os.makedirs(self.path, exist_ok=True)

            with open(filename, "w", encoding="UTF-8") as fp:
                json.dump(self.data, fp)
        except:
            self.logger.error(f"[{self._username}@{self.remote_addr}] Unable to place token - {self.token}")
            self.logger.debug(str(sys.exc_info()[0]))
            self.logger.debug(str(traceback.format_exc()))
            return False
        
        return True

    #def _remove_token_data(self):
    #    if self.token is None or self._username is None:
    #        return False
    #    
    #    try:
    #        # using sha1() simply to insure the filename is a string without special chars in it
    #        filename = os.path.join(self.path, f"{hashlib.sha1(self._username.encode()).hexdigest()}.json")
    #        if os.path.exists(filename):
    #            os.remove(filename)
    #
    #    except:
    #        return False
    #
    #    return True
    
    #def purge(self):
    #    if os.path.exists(self.path):
    #        file_list = os.listdir(self.path)
    #        for file_name in file_list:
    #            if file_name.endswith(".json"):
    #                with open(os.path.join(self.path, file_name), "r", encoding="UTF-8") as fp:
    #                    data = json.load(fp)
    #                
    #                if self.is_expired(data.get("expires")):
    #                    username = data.get("username")
    #                    token = data.get("token")
    #                    file_name_base = file_name.rsplit('.', 1)[0]
    #                    logging.info(f"[{username}] Expired token purged. - {token}")
    #                    os.remove(os.path.join(self.path, file_name))
    #    
    #    return True


class RedisTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.host = os.environ.get("TOKENIZER_HOST", kwargs.get("host", "localhost"))
        self.port = os.environ.get("TOKENIZER_PORT", kwargs.get("port", 6379))

        import redis
        self.conn = redis.Redis(
            host=self.host,
            port=self.port,
            ssl=(os.environ.get("TOKENIZER_SSL", str(kwargs.get("options", {}).get("ssl", False))).lower() == "true"),
            ssl_cert_reqs="none",
            decode_responses=True
        )

    def _get_token_data(self):
        if self.token is None or self._username is None:
            return super()._get_token_data()
        
        data = None

        try:
            d = self.conn.get(self._username)
            data = json.loads(d if isinstance(d, str) else "{}")

        except:
            return super()._get_token_data()

        return data

    def _put_token_data(self):
        if self.token is None or self._username is None or self.data is None:
            self.logger.error(f"[{self._username}@{self.remote_addr}] Unable to place token - {self.token}")
            return False
        
        try:
            self.conn.set(self._username, json.dumps(self.data))
        except:
            self.logger.error(f"[{self._username}@{self.remote_addr}] Unable to place token - {self.token}")
            self.logger.debug(str(sys.exc_info()[0]))
            self.logger.debug(str(traceback.format_exc()))
            return False
        
        return True

    #def _remove_token_data(self):
    #    if self.token is None or self._username is None:
    #        return False
    #    
    #    try:
    #        self.conn.delete(self.token)
    #    except:
    #        return False
    #
    #    return True 
    
    #def purge(self):
    #    cursor = 0
    #    while True:
    #        cursor, tokens = self.conn.scan(cursor=cursor)
    #        for token in tokens:
    #            data = json.loads(self.conn.get(token))
    #            if data.get("type", "") == "token":
    #                if self.is_expired(data.get("expires")):
    #                    username = data.get("username")
    #                    try:
    #                        self.conn.delete(token)
    #                        logging.info(f"[{username}] Expired token purged. - {token}")
    #                    except:
    #                        logging.error(f"[{username}] Unable to remove expired token - {token}")
    #
    #        if cursor == 0:
    #            break
    #
    #    return True


class DynamoDBTokens(Tokens):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        import boto3
        boto3.set_stream_logger('boto3', logging.WARNING)
        boto3.set_stream_logger('botocore', logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        self.table_name = os.environ.get("TOKENIZER_TABLE", kwargs.get("table", "tokens"))

        session = boto3.Session(**cfg.aws_credentials(kwargs))
        self.conn = session.client('dynamodb', region_name=cfg.aws_region_name(kwargs))

    def _get_token_data(self):
        if self.token is None or self._username is None:
            return super()._get_token_data()
        
        data = super()._get_token_data()

        try:
            #self.logger.debug(f"Getting token from dynamodb key={self._username}")
            response = self.conn.get_item(TableName=self.table_name, Key={ "username": { "S": str(self._username) } }, ConsistentRead=True)
            #self.logger.debug(f"Token data = {response['Item'].get('data')}")
            d = response["Item"].get("data").get("S")
            data = json.loads(d if isinstance(d, str) else "{}")
        except:
            return super()._get_token_data()

        return data

    def _put_token_data(self):
        
        #stack = traceback.extract_stack()
        #formatted_stack = traceback.format_list(stack)
        #self.logger.debug("\n".join(formatted_stack))
        
        if self.token is None or self._username is None or self.data is None:
            self.logger.error(f"[{self._username}@{self.remote_addr}] Unable to place token - {self.token}")
            return False
        
        try:
            #self.logger.debug(f"Sending {self.username} and {self.token} and {self.data}")
            self.conn.put_item(TableName=self.table_name, Item={ "username": { "S": str(self._username) }, "data": { "S": json.dumps(self.data) } })
        except:
            self.logger.error(f"[{self._username}@{self.remote_addr}] Unable to place token - {self.token}")
            self.logger.debug(str(sys.exc_info()[0]))
            self.logger.debug(str(traceback.format_exc()))
            return False
        
        return True

    #def _remove_token_data(self):
    #    if self.token is None or self._username is None:
    #        return False
    #
    #    try:
    #        self.conn.delete_item(TableName=self.table_name, Key={ "token": { "S": self.token } })
    #    except:
    #        return False
    #    
    #    return True
    
    #def purge(self):
    #    try:
    #        response = self.conn.scan(TableName=self.table_name)
    #        for item in response["Items"]:
    #            data = json.loads(item.get("data").get("S"))
    #            if data.get("type", "") == "token":
    #                if self.is_expired(data.get("expires")):
    #                    username = data.get("username")
    #                    token = item.get("token")
    #                    
    #                    try:
    #                        self.conn.delete_item(TableName=self.table_name, Key={ "token": token })
    #                        logging.info(f"[{username}] Expired token purged. - {token}")
    #                    except:
    #                        logging.error(f"[{username}] Unable to remove expired token - {token}")
    #    except:
    #        pass
    #    
    #    return True


def get_tokenizer(connection_details):
    if connection_details.get("type", "local") == "local":
        return LocalTokens(**connection_details)
    
    if connection_details.get("type", "local") == "redis":
        return RedisTokens(**connection_details)
    
    if connection_details.get("type", "local") == "dynamodb":
        return DynamoDBTokens(**connection_details)
    
    return Tokens(**connection_details)


#tokenizer = get_tokenizer(cfg.sys_tokenizer)
