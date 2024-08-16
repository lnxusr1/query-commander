import os
import sys
import logging
import json

from functions import process_request
from core.config import settings as cfg
from core.interactions import Request, Response
from core.helpers import get_page_content

VERSION = (0, 5, 1)
__version__ = ".".join([str(x) for x in VERSION])

logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %z',
    format='%(levelname)s - %(message)s', # %(name)s - %(asctime)s 
    level=logging.DEBUG)

logging.getLogger("psycopg.pq").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

def as_cgi():
    if os.environ.get("REQUEST_METHOD", "GET") == "GET":
        import cgi

        form = cgi.FieldStorage()
        path_value = form.getvalue("page")

        if path_value is None or str(path_value) == "":
            path_value = "index.html"

        page_content, headers = get_page_content(path_value)

        for item in headers:
            logging.info(f"{item}: {headers[item]}\n")
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
    if event["httpMethod"] == "GET":
        page_content, headers = get_page_content(event["queryStringParameters"].get("page", "index"))
        if headers["Content-Type"] in ["image/jpeg", "image/png"]:
            import base64
            return {
                'statusCode': '200',
                'body': base64.b64encode(page_content).decode('utf-8'),
                'headers': headers,
                'isBase64Encoded': True
            }
        else:
            return {
                'statusCode': '200',
                'body': page_content,
                'headers': headers
            }

    headers = {}
    for hdr in event.get("headers", {}):
        headers[hdr.upper()] = event.get("headers", {}).get(hdr, "")

    headers["REMOTE_ADDR"] = event.get("requestContext", {}).get("identity", {}).get("sourceIp", "")
    if "COOKIE" in headers:
        headers["HTTP_COOKIE"] = headers.get("COOKIE")

    request = Request(**headers)
    request.set_data(event.get("body", "{}"))
    resp = Response()

    try:
        process_request(request, resp)
    except:
        return {
            'statusCode': '200',
            'body': json.dumps({ "ok": False, "error": "An internal error occurred." }),
            'headers': { "Content-Type": "application/json" }
        }

    return {
        'statusCode': '200',
        'body': json.dumps(resp.raw_data),
        'headers': resp.headers
    }