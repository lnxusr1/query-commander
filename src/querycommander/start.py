import os
import sys
import logging
import json
import traceback
import http.cookies

from querycommander import __version__
from querycommander.functions import process_request
from querycommander.core.config import settings as cfg
from querycommander.core.interactions import Request, Response
from querycommander.core.helpers import get_page_content

logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %z',
    format='%(levelname)s - %(message)s', # %(name)s - %(asctime)s 
    level=logging.DEBUG)

logging.getLogger("psycopg.pq").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

logger = logging.getLogger("START")
logger.setLevel(cfg.log_level)


def send_socket_message(endpoint_url, connection_id, message):
    import boto3
    apigateway_client = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=endpoint_url
    )
    
    apigateway_client.post_to_connection(ConnectionId=connection_id, Data=json.dumps(message).encode('utf-8'))


def as_cgi():
    os.environ["AWS_LAMBDA"] = "OFF"
    if os.environ.get("REQUEST_METHOD", "GET") == "GET":
        import cgi

        form = cgi.FieldStorage()
        path_value = form.getvalue("page")

        if path_value is None or str(path_value) == "":
            path_value = "index.html"

        logger.info(f"[{os.environ.get('REMOTE_ADDR')}] Request for {path_value}")
        page_content, headers = get_page_content(path_value)

        for item in headers:
            sys.stdout.buffer.write(f"{item}: {headers[item]}\n".encode())

        sys.stdout.buffer.write("\n".encode())
        if headers["Content-Type"] in ["image/png", "image/jpeg"]:
            sys.stdout.buffer.write(page_content)
        else:
            if path_value == "script.js":
                page_content = page_content.replace("${VERSION}", __version__)

            if path_value == "index.html":
                page_content = page_content.replace("<!-- fontawesome -->", cfg.cdn_fontawesome)
                page_content = page_content.replace("<!-- jquery -->", cfg.cdn_jquery)

                if cfg.codemirror:
                    page_content = page_content.replace("<!-- codemirror_css -->", cfg.cdn_codemirror_css)
                    page_content = page_content.replace("<!-- codemirror_js -->", cfg.cdn_codemirror_js)
                    page_content = page_content.replace("<!-- codemirror_sql -->", cfg.cdn_codemirror_sql)

                page_content = page_content.replace("<!-- page_login_bg -->", cfg.img_login_bg)
                page_content = page_content.replace("<!-- page_logo -->", cfg.img_logo)
                page_content = page_content.replace("<!-- page_logo_sm -->", cfg.img_logo_sm)
                page_content = page_content.replace("<!-- page_favicon -->", cfg.img_favicon)
                page_content = page_content.replace("##APP_NAME##", cfg.app_name)

            sys.stdout.buffer.write(page_content.encode())
        sys.exit()

    request = Request(**os.environ)
    resp = Response()

    if request.headers.get("CONTENT_LENGTH", 0) > 0:
        request.set_data(sys.stdin.read(request.headers.get("CONTENT_LENGTH")))
    else:
        logging.error(f"Invalid request from {request.host}")
        resp.output({ "ok": False })
        resp.send()
        sys.exit()

    process_request(request, resp)
    resp.send()


def as_lambda(event, context):
    os.environ["AWS_LAMBDA"] = "ON"
    cfg.is_lambda = True
    cfg.context = context

    headers = {}
    headers["REMOTE_ADDR"] = event.get("requestContext", {}).get("identity", {}).get("sourceIp", "")

    if event.get("httpMethod", "") == "GET":
 
        path_value = event["queryStringParameters"].get("page", "index.html") if isinstance(event["queryStringParameters"], dict) else "index.html"
        logger.info(f"[{headers.get('REMOTE_ADDR')}] Request for {path_value}")

        page_content, hdrs = get_page_content(path_value)

        if hdrs["Content-Type"] in ["image/jpeg", "image/png"]:
            import base64
            return {
                'statusCode': '200',
                'body': base64.b64encode(page_content).decode('utf-8'),
                'headers': hdrs,
                'isBase64Encoded': True
            }
        else:

            if path_value == "script.js":
                page_content = page_content.replace("${VERSION}", __version__)

            if path_value == "index.html":
                page_content = page_content.replace("<!-- fontawesome -->", cfg.cdn_fontawesome)
                page_content = page_content.replace("<!-- jquery -->", cfg.cdn_jquery)

                if cfg.codemirror:
                    page_content = page_content.replace("<!-- codemirror_css -->", cfg.cdn_codemirror_css)
                    page_content = page_content.replace("<!-- codemirror_js -->", cfg.cdn_codemirror_js)
                    page_content = page_content.replace("<!-- codemirror_sql -->", cfg.cdn_codemirror_sql)

                page_content = page_content.replace("<!-- page_login_bg -->", cfg.img_login_bg)
                page_content = page_content.replace("<!-- page_logo -->", cfg.img_logo)
                page_content = page_content.replace("<!-- page_logo_sm -->", cfg.img_logo_sm)
                page_content = page_content.replace("<!-- page_favicon -->", cfg.img_favicon)
                page_content = page_content.replace("##APP_NAME##", cfg.app_name)

            return {
                'statusCode': '200',
                'body': page_content,
                'headers': hdrs
            }

    my_body = "{}"
    if "body" in event:
        if "isBase64Encoded" in event:
            if event.get("isBase64Encoded", False):
                import base64
                my_body = base64.b64decode(event.get("body")).decode("UTF-8")
            else:
                my_body = event.get("body")
        else:
            my_body = event.get("body")

    if event.get("httpMethod", "") == "POST":
        for hdr in event.get("headers", {}):
            headers[hdr.upper().replace("-","_")] = event.get("headers", {}).get(hdr, "")

        if "COOKIE" in headers:
            headers["HTTP_COOKIE"] = headers.get("COOKIE")

    if "httpMethod" not in event or event.get("httpMethod", "") == "":
        try:
            my_body_data = json.loads(my_body)
        except:
            my_body_data = {}

        headers["is_socket"] = True
        headers["CONTENT_TYPE"] = "application/json"
        headers["token"] = my_body_data.get("token")
        headers["username"] = my_body_data.get("username")
        domain_name = event.get('requestContext', {}).get('domainName','')
        stage = event.get("requestContext", {}).get("stage", "")
        headers["socket_addr"] = f"https://{domain_name}/{stage}"
        headers["connection_id"] = event.get("requestContext", {}).get("connectionId")
        headers["request_id"] = event.get("requestContext", {}).get("requestId")
        headers["message_id"] = event.get("requestContext", {}).get("messageId")

    request = Request(**headers)
    request.set_data(my_body)
    resp = Response(is_socket=request.is_socket)

    try:
        process_request(request, resp)
    except:
        logger.error(f"[{headers['REMOTE_ADDR']}] - {str(sys.exc_info()[0])}")
        logger.debug(str(traceback.format_exc()))

        body_data = json.dumps({ "ok": False, "error": "An internal error occurred." })
        if resp.is_socket:
            send_socket_message(request.socket_addr, request.connection_id, body_data)

        return {
            'statusCode': '200',
            'body': body_data,
            'headers': { "Content-Type": "application/json" }
        }

    body_data = resp.raw_data
    v_headers = {}
    mv_headers = {}

    for item in resp.headers:
        if isinstance(resp.headers.get(item), list):
            mv_headers[item] = resp.headers.get(item)
        else:
            v_headers[item] = resp.headers.get(item)

    if resp.is_socket:
        send_socket_message(request.socket_addr, request.connection_id, body_data)

    return {
        'statusCode': '200',
        'body': json.dumps(body_data),
        'headers': v_headers,
        'multiValueHeaders': mv_headers
    }
