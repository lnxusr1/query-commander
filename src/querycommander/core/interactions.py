import json
import http.cookies
from core.tokenizer import tokenizer


class Response:
    def __init__(self, **kwargs):
        hdrs = kwargs.get("headers", { "Content-Type": "application/json" })
        if isinstance(hdrs, dict):
            self.headers = hdrs

        self.data = kwargs.get("data")
        self.raw_data = None
        self.extend = None
        self.cookie = None

    def add_header(self, name, value):
        if name is not None and value is not None:
            self.headers[str(name)] = str(value)

        return True

    def output(self, data=None, extend=None):
        self.raw_data = data
        self.extend = extend

        self.add_header("Access-Control-Allow-Origin", "*")
        cookie = tokenizer.cookie(extend=self.extend)
        if cookie is not None:
            self.add_header(cookie.split(":", 1)[0].strip(), cookie.split(":", 1)[1].strip())

    def send(self):
        data = self.raw_data

        if len(self.headers) == 0:
            print("Content-Type: text/html")

        for item in self.headers:
            print(f"{str(item.rstrip())}: {str(self.headers.get(item))}")
        
#        if self.cookie is not None:
#            print(str(self.cookie).strip())
    
        print("")
        if data is None and self.data is None:
            print("")

        if data is None and self.data is not None:
            data = self.data

        if isinstance(data, list) or isinstance(data, dict):
            print(json.dumps(data))
        else:
            print(str(data))


class Request:
    def __init__(self, **kwargs):
        self.raw_data = None
        self.json_data = {}
        self.token = None
        self.username = None

        self.headers = {}

        self.headers["CONTENT_TYPE"] = kwargs.get("CONTENT_TYPE", "text/html")
        self.headers["REQUEST_METHOD"] = kwargs.get("REQUEST_METHOD", "GET")
        self.headers["HTTP_COOKIE"] = kwargs.get("HTTP_COOKIE", "")
        self.headers["REMOTE_ADDR"] = kwargs.get("REMOTE_ADDR", "")

        content_length = str(kwargs.get("CONTENT_LENGTH", "0"))
        self.headers["CONTENT_LENGTH"] = int(content_length) if content_length.isnumeric() else 0

        try:
            self.cookies = http.cookies.SimpleCookie(self.headers["HTTP_COOKIE"])
        except:
            self.cookies = {}

        try:
            if "token" in self.cookies:
                self.token = self.cookies["token"].value
        except:
            pass

        try:
            if "username" in self.cookies:
                self.username = self.cookies["username"].value
        except:
            pass

    def set_data(self, data):
        if data is not None:
            self.raw_data = data
            if (str(self.headers.get("CONTENT_TYPE"))).lower() == "application/json" and len(self.raw_data) > 0:
                self.json_data = json.loads(self.raw_data)

    #def set_user(self, username):
    #    self.json_data["username"] = username

    @property
    def host(self):
        return self.headers.get("REMOTE_ADDR")
