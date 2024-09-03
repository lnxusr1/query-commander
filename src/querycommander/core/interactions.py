import json
import logging
import http.cookies
#from querycommander.core.tokenizer import tokenizer

logger = logging.getLogger("INTERACTIONS")


class Response:
    def __init__(self, **kwargs):
        hdrs = kwargs.get("headers", { "Content-Type": "application/json" })
        if isinstance(hdrs, dict):
            self.headers = hdrs

        self.is_socket = kwargs.get("is_socket", False)
        self.data = kwargs.get("data")
        self.raw_data = None
        self.extend = None
        self.cookie = None
        self.req_type = str(kwargs.get("req_type", ""))
        self.tokenizer = None

    def add_header(self, name, value):
        if name is not None and value is not None:
            if str(name) in self.headers:
                if isinstance(self.headers[str(name)], list):
                    self.headers[str(name)].append(str(value))
                else:
                    self.headers[str(name)] = [self.headers[str(name)], str(value)]
            else:
                self.headers[str(name)] = str(value)

        return True

    def output(self, data=None, extend=None):
        self.raw_data = data
        self.extend = extend

        #self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Cache-Control", "max-age=0, no-cache, no-store, must-revalidate")
        self.add_header("Pragma", "no-cache")
        self.add_header("Expires", "0")
        self.add_header('Access-Control-Allow-Origin', '*')
        self.add_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        self.add_header('Referrer-Poilcy', 'strict-origin')
        self.add_header('X-Content-Type-Options', 'nosniff')
        self.add_header('X-Frame-Options', 'deny')
        self.add_header('X-XSS-Protection', '1; mode=block')

        if self.tokenizer is not None:
            cookie = self.tokenizer.cookie(extend=self.extend, req_type=self.req_type)
            if self.req_type in ["login","logout"]:
                if cookie is not None:
                    import logging
                    if "\n" in cookie:
                        cookies = cookie.split("\r\n")
                        for c in cookies:
                            self.add_header(c.split(":", 1)[0].strip(), c.split(":", 1)[1].strip())
                    else:
                        self.add_header(cookie.split(":", 1)[0].strip(), cookie.split(":", 1)[1].strip())

    def send(self):
        data = self.raw_data

        if len(self.headers) == 0:
            print("Content-Type: text/html")

        for item in self.headers:
            if isinstance(self.headers[item], list):
                for si in self.headers[item]:
                    print(f"{str(item.rstrip())}: {str(si)}")
            else:
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
        self.is_socket = kwargs.get("is_socket", False)
        self.raw_data = None
        self.json_data = {}
        self.token = kwargs.get("token")
        self.username = kwargs.get("username")
        self.socket_addr = kwargs.get("socket_addr")
        self.connection_id = kwargs.get("connection_id")
        self.request_id = kwargs.get("request_id")
        self.message_id = kwargs.get("message_id")

        self.headers = {}

        self.headers["CONTENT_TYPE"] = kwargs.get("CONTENT_TYPE", "text/html")
        self.headers["REQUEST_METHOD"] = kwargs.get("REQUEST_METHOD", "GET")
        self.headers["HTTP_COOKIE"] = kwargs.get("HTTP_COOKIE", "")
        self.headers["REMOTE_ADDR"] = kwargs.get("REMOTE_ADDR", "")

        content_length = str(kwargs.get("CONTENT_LENGTH", "0"))
        self.headers["CONTENT_LENGTH"] = int(content_length) if content_length.isnumeric() else 0

        if self.headers.get("HTTP_COOKIE") is not None:
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

        logger.debug(f"Token = {self.username}")
        logger.debug(f"Token = {self.token}")

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
