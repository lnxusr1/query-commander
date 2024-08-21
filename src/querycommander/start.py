import os
import sys
import logging
import json
import traceback

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

def as_cgi():
    if os.environ.get("REQUEST_METHOD", "GET") == "GET":
        import cgi

        form = cgi.FieldStorage()
        path_value = form.getvalue("page")

        if path_value is None or str(path_value) == "":
            path_value = "index.html"

        logger.info(f"Request for {path_value}")
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

    headers = {}
    for hdr in event.get("headers", {}):
        headers[hdr.upper().replace("-","_")] = event.get("headers", {}).get(hdr, "")

    headers["REMOTE_ADDR"] = event.get("requestContext", {}).get("identity", {}).get("sourceIp", "")
    if "COOKIE" in headers:
        headers["HTTP_COOKIE"] = headers.get("COOKIE")

    if event["httpMethod"] == "GET":
        
        path_value = event["queryStringParameters"].get("page", "index.html") if isinstance(event["queryStringParameters"], dict) else "index.html"
        logger.info(f"Request for {path_value}")

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

    request = Request(**headers)
    request.set_data(my_body)
    resp = Response()

    try:
        process_request(request, resp)
    except:
        logger.error(f"[{headers['REMOTE_ADDR']}] - {str(sys.exc_info()[0])}")
        logger.debug(str(traceback.format_exc()))
        return {
            'statusCode': '200',
            'body': json.dumps({ "ok": False, "error": "An internal error occurred." }),
            'headers': { "Content-Type": "application/json" }
        }

    body_data = json.dumps(resp.raw_data)
    v_headers = {}
    mv_headers = {}

    for item in resp.headers:
        if isinstance(resp.headers.get(item), list):
            mv_headers[item] = resp.headers.get(item)
        else:
            v_headers[item] = resp.headers.get(item)

    return {
        'statusCode': '200',
        'body': body_data,
        'headers': v_headers,
        'multiValueHeaders': mv_headers
    }