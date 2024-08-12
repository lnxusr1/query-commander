import os
import tempfile
import hashlib
import json
import logging
import datetime

from core.helpers import get_utc_now
from core.config import settings as cfg


class Profiler:
    def __init__(self, **kwargs):
        self.format_version = 2
        self.username = None
        self.settings = kwargs
        self.data = None

    def _get_profile_data(self):
        # OVERRIDE THIS METHOD
        return {}
    
    def _put_profile_data(self):
        # OVERRIDE THIS METHOD
        return False
    
    def _remove_profile_data(self):
        # OVERRIDE THIS METHOD
        return False

    def _get(self):
        if self.data is not None:
            return
        
        self.data = self._get_profile_data()
        
    def get(self, name, default_value=None):
        self._get()
        return self.data.get(name, default_value)
    
    def get_records_remaining(self):
        if cfg.rate_limit_period <= 0 and cfg.rate_limit_records <= 0:
            return cfg.records_per_request
        
        timestamp = get_utc_now() - datetime.timedelta(minutes=cfg.rate_limit_period)
        history_data = self.get("history", [])
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

    def update(self):
        self._get()
        self.set("format_version", self.format_version)
        self.set("type", "profile")

        return self._put_profile_data()
    
    def remove(self):
        self._get()
        return self._remove_profile_data()

    def set_username(self, value):
        if value is not None and len(str(value)) >= 4:
            self.username = value
        else:
            self.username = None

    def set(self, name, value=None):
        self._get()
        if name == "tabs":
            if isinstance(value, list) and len(value) < 10: # max 10 tabs
                for x in value:
                    if not isinstance(x, dict):
                        return
                    if len(x) != 3:
                        return
                    if x.get("name") is None or x.get("content") is None:
                        return
                    x["name"] = str(x.get("name"))[0:255]
                    x["database"] = str(x.get("database"))[0:100]
                    x["content"] = str(x.get("content"))[0:20000]
            else:
                return

        if name == "settings":
            if isinstance(value, dict) and len(value) == 0:
                pass
            else:
                return

        if name == "history":
            if isinstance(value, list):
                for x in value:
                    if not isinstance(x, list):
                        return
                    
                    if len(x) != 2:
                        return
                    
                    if isinstance(x[1], int):
                        return
                    
                    try:
                        s = datetime.datetime.strptime(str(x[0]), "%Y-%m-%d %H:%M:%S")
                    except:
                        return

        self.data[name] = value


class LocalProfiler(Profiler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.path = kwargs.get("path", os.path.join(tempfile.gettempdir(), "profiles"))

    def _get_profile_data(self):
        if self.username is None:
            return super()._get_profile_data()
        
        data = super()._get_profile_data()

        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self.username.encode()).hexdigest()}.json")
            if os.path.exists(filename):
                with open(filename, "r", encoding="UTF-8") as fp:
                    data = json.load(fp)
        except:
            return super()._get_profile_data()

        return data
    
    def _put_profile_data(self):
        if self.username is None or self.data is None:
            return False
        
        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self.username.encode()).hexdigest()}.json")
            os.makedirs(self.path, exist_ok=True)

            with open(filename, "w", encoding="UTF-8") as fp:
                json.dump(self.data, fp)
        except:
            return False
        
        return True
    
    def _remove_profile_data(self):
        if self.username is None or self.data is None:
            return False
        
        try:
            # using sha1() simply to insure the filename is a string without special chars in it
            filename = os.path.join(self.path, f"{hashlib.sha1(self.username.encode()).hexdigest()}.json")
            if os.path.exists(filename):
                os.remove(filename)

        except:
            return False

        return True
    

class DynamoDBProfiler(Profiler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        import boto3
        boto3.set_stream_logger('boto3', logging.WARNING)
        boto3.set_stream_logger('botocore', logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        self.table_name = kwargs.get("table", "profiles")

        session = boto3.Session(**cfg.aws_credentials(kwargs))
        self.conn = session.client('dynamodb', region_name=cfg.aws_region_name(kwargs))

    def _get_profile_data(self):
        if self.username is None:
            return super()._get_profile_data()
        
        data = super()._get_profile_data()

        try:
            response = self.conn.get_item(TableName=self.table_name, Key={ "username": { "S": str(self.username) } })
            d = response["Item"].get("data").get("S")
            data = json.loads(d if isinstance(d, str) else "{}")
        except:
            return super()._get_profile_data()

        return data

    def _put_profile_data(self):
        if self.username is None or self.data is None:
            return False
        
        try:
            self.conn.put_item(TableName=self.table_name, Item={ "username": { 'S': self.username}, "data": {'S': json.dumps(self.data) }})
        except:
            return False
        
        return True
    
    def _remove_profile_data(self):
        if self.username is None:
            return False

        try:
            self.conn.delete_item(TableName=self.table_name, Key={ "username": { "S": self.username } })
        except:
            return False
        
        return True


def get_profiler(connection_details):
    if connection_details.get("type", "local") == "local":
        return LocalProfiler(**connection_details)
    if connection_details.get("type", "local") == "dynamodb":
        return DynamoDBProfiler(**connection_details)
        
        
    return Profiler(**connection_details)


profiler = get_profiler(cfg.sys_profiler)