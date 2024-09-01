import os
import json
import yaml
import logging

from querycommander.core.connections import Connections


def get_websocket_apis_invoking_lambda(context):
    import boto3

    # Get the Lambda function ARN
    function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
    #function_version = os.environ['AWS_LAMBDA_FUNCTION_VERSION']
    region = os.environ['AWS_REGION']
    account_id = context.invoked_function_arn.split(":")[4]
    lambda_arn = f"arn:aws:lambda:{region}:{account_id}:function:{function_name}"

    # Create a client for API Gateway V2
    client = boto3.client('apigatewayv2')

    # List all WebSocket APIs
    response = client.get_apis()

    # List to hold APIs that invoke the current Lambda function
    websocket_apis_invoke_lambda = []

    for api in response['Items']:
        api_id = api['ApiId']

        if api['ProtocolType'] == "WEBSOCKET":
            # Get all integrations for this API
            stages = client.get_stages(ApiId=api_id)
            stages = [x.get("StageName") for x in stages["Items"]]
            if len(stages) == 1:

                integrations = client.get_integrations(ApiId=api_id)
                for integration in integrations['Items']:

                    # Check if the integration is a Lambda proxy integration and if the URI matches the Lambda ARN
                    if integration['IntegrationType'] == 'AWS_PROXY' and f"{lambda_arn}/invocations" in integration['IntegrationUri']:
                        api_endpoint = f"{api['ApiEndpoint']}/{stages[0]}"
                        if api_endpoint not in websocket_apis_invoke_lambda:
                            websocket_apis_invoke_lambda.append(api_endpoint)

    if len(websocket_apis_invoke_lambda) == 1:
        return websocket_apis_invoke_lambda[0]
    else:
        return ""


class Settings:
    CONFIG_PATH = os.environ.get("QRYCOMM_CONFIG_PATH", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "config")))

    def __init__(self):
        self.data = {}

        if os.path.exists(os.path.join(self.CONFIG_PATH, "settings.yml")):
            with open(os.path.join(self.CONFIG_PATH, "settings.yml"), "r", encoding="UTF-8") as fp:
                self.data = yaml.safe_load(fp)

        self._connections = Connections(global_settings=self, **self.data.get("connections", {}))
        #self.web_socket = self.data.get("settings", {}).get("web_socket", "")
        self.is_lambda = False
        self.context = None

    def sys_connections(self, conn_name=None):
        if conn_name is None:
            return self._connections.list()

        return self._connections.get(conn_name)

    @property
    def codemirror(self):
        if str(os.environ.get("CODEMIRROR", self.data.get("settings", {}).get("codemirror", False))).lower() == "disable":
            return False
        
        return True

    @property
    def img_login_bg(self):
        return os.environ.get("IMG_LOGIN_BG", self.data.get("settings", {}).get("img_login_bg", "?page=bglogin.jpg"))

    @property
    def img_logo(self):
        return os.environ.get("IMG_LOGO", self.data.get("settings", {}).get("img_logo", "?page=logo.png"))
    
    @property
    def img_logo_sm(self):
        return os.environ.get("IMG_LOGO_SM", self.data.get("settings", {}).get("img_logo_sm", "?page=favicon.svg"))
    
    @property
    def img_favicon(self):
        return os.environ.get("IMG_FAVICON", self.data.get("settings", {}).get("img_favicon", "?page=favicon.svg"))

    @property
    def app_name(self):
        return os.environ.get("APP_NAME", self.data.get("settings", {}).get("application_name", "Query Commander"))

    @property
    def web_socket(self):
        wss = os.environ.get("WEB_SOCKET", self.data.get("settings", {}).get("web_socket", ""))
        if self.is_lambda and (wss is None or len(str(wss)) <= 5):
            return f"{get_websocket_apis_invoking_lambda(self.context)}"
        
        return wss

    @property
    def profiles(self):
        p = os.environ.get("PROFILES", self.data.get("settings", {}).get("profiles", "enable"))
        if str(p).lower() in ["enable", "enabled", ""]:
            return True
        
        return False
    
    @property
    def sys_authenticator(self):
        return self.data.get("authenticator", { "type": "local" })
    
    @property
    def sys_tokenizer(self):
        tk_data = self.data.get("tokenizer", { "type": "local" })
        tk_data["type"] = os.environ.get("TOKENIZER_TYPE", tk_data.get("type"))
        return tk_data
    
    @property
    def sys_profiler(self):
        return self.data.get("profiler", { "type": "local" })

    @property
    def sys_mappings(self):
        return self.data.get("mappings", {})
    
    @property
    def records_per_request(self):
        return int(os.environ.get('RECORDS_PER_REQUEST', self.data.get("settings", {}).get("records_per_request", 200)))
    
    @property
    def rate_limit_records(self):
        return int(os.environ.get('RATE_LIMIT_RECORDS', self.data.get("settings", {}).get("rate_limit", {}).get("records", -1)))

    @property
    def rate_limit_period(self):
        return int(os.environ.get('RATE_LIMIT_PERIOD', self.data.get("settings", {}).get("rate_limit", {}).get("period", -1)))
    
    @property
    def cdn_fontawesome(self):
        far = self.data.get("settings", {}).get("cdns", {}).get("fontawesome", {})
        fa = {
            "href": os.environ.get("FONTAWESOME_URL", far.get("url", "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css")),
            "integrity": os.environ.get("FONTAWESOME_INTEGRITY", far.get("integrity", "sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA==")),
            "crossorigin": os.environ.get("FONTAWESOME_CROSSORIGIN", far.get("crossorigin", "anonymous")),
            "referrerpolicy": os.environ.get("FONTAWESOME_REFERRERPOLICY", far.get("referrerpolicy", "no-referrer"))
        }
        return f"<link rel=\"stylesheet\" " + " ".join([f"{x}=\"{fa[x]}\"" for x in fa]) + " />"

    @property
    def cdn_jquery(self):
        far = self.data.get("settings", {}).get("cdns", {}).get("jquery", {})
        fa = {
            "src": os.environ.get("JQUERY_URL", far.get("url", "https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js")),
            "integrity": os.environ.get("JQUERY_INTEGRITY", far.get("integrity", "sha512-v2CJ7UaYy4JwqLDIrZUI/4hqeoQieOmAZNXBeQyjo21dadnwR+8ZaIJVT8EE2iyI61OV8e6M8PP2/4hpQINQ/g==")),
            "crossorigin": os.environ.get("JQUERY_CROSSORIGIN", far.get("crossorigin", "anonymous")),
            "referrerpolicy": os.environ.get("JQUERY_REFERRERPOLICY", far.get("referrerpolicy", "no-referrer"))
        }
        return f"<script " + " ".join([f"{x}=\"{fa[x]}\"" for x in fa]) + "></script>"

    @property
    def cdn_codemirror_css(self):
        far = self.data.get("settings", {}).get("cdns", {}).get("codemirror_css", {})
        fa = {
            "href": os.environ.get("CODEMIRROR_CSS_URL", far.get("url", "https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.css")),
            "integrity": os.environ.get("CODEMIRROR_CSS_INTEGRITY", far.get("integrity", "sha512-uf06llspW44/LZpHzHT6qBOIVODjWtv4MxCricRxkzvopAlSWnTf6hpZTFxuuZcuNE9CBQhqE0Seu1CoRk84nQ==")),
            "crossorigin": os.environ.get("CODEMIRROR_CSS_CROSSORIGIN", far.get("crossorigin", "anonymous")),
            "referrerpolicy": os.environ.get("CODEMIRROR_CSS_REFERRERPOLICY", far.get("referrerpolicy", "no-referrer"))
        }
        return f"<link rel=\"stylesheet\" " + " ".join([f"{x}=\"{fa[x]}\"" for x in fa]) + " />"

    @property
    def cdn_codemirror_js(self):
        far = self.data.get("settings", {}).get("cdns", {}).get("codemirror_js", {})
        fa = {
            "src": os.environ.get("CODEMIRROR_JS_URL", far.get("url", "https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.js")),
            "integrity": os.environ.get("CODEMIRROR_JS_INTEGRITY", far.get("integrity", "sha512-8RnEqURPUc5aqFEN04aQEiPlSAdE0jlFS/9iGgUyNtwFnSKCXhmB6ZTNl7LnDtDWKabJIASzXrzD0K+LYexU9g==")),
            "crossorigin": os.environ.get("CODEMIRROR_JS_CROSSORIGIN", far.get("crossorigin", "anonymous")),
            "referrerpolicy": os.environ.get("CODEMIRROR_JS_REFERRERPOLICY", far.get("referrerpolicy", "no-referrer"))
        }
        return f"<script " + " ".join([f"{x}=\"{fa[x]}\"" for x in fa]) + "></script>"

    @property
    def cdn_codemirror_sql(self):
        far = self.data.get("settings", {}).get("cdns", {}).get("codemirror_sql", {})
        fa = {
            "src": os.environ.get("CODEMIRROR_SQL_URL", far.get("url", "https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/sql/sql.min.js")),
            "integrity": os.environ.get("CODEMIRROR_SQL_INTEGRITY", far.get("integrity", "sha512-JOURLWZEM9blfKvYn1pKWvUZJeFwrkn77cQLJOS6M/7MVIRdPacZGNm2ij5xtDV/fpuhorOswIiJF3x/woe5fw==")),
            "crossorigin": os.environ.get("CODEMIRROR_SQL_CROSSORIGIN", far.get("crossorigin", "anonymous")),
            "referrerpolicy": os.environ.get("CODEMIRROR_SQL_REFERRERPOLICY", far.get("referrerpolicy", "no-referrer"))
        }
        return f"<script " + " ".join([f"{x}=\"{fa[x]}\"" for x in fa]) + "></script>"

    @property
    def log_level(self):
        lvl = str(os.environ.get('LOG_LEVEL', self.data.get("settings", {}).get("log_level", "info"))).lower()

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
        return in_settings.get("aws_region_name", os.environ.get("AWS_REGION_NAME", self.sys_settings("aws_region_name")))

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
                "profile_name": os.environ.get("AWS_PROFILE_NAME", self.sys_settings("aws_profile_name"))
            }

        if self.sys_settings("aws_access_key") is not None:
            return { 
                "aws_access_key_id": os.environ.get('AWS_ACCESS_KEY', self.sys_settings("aws_access_key")), 
                "aws_secret_access_key": os.environ.get('AWS_SECRET_KEY', self.sys_settings("aws_secret_key"))
            }

        return {}

def load_settings():
    s = Settings()
    return s

settings = load_settings()
