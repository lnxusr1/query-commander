#!/usr/bin/env python

import os
import sys
import logging
import json

from functions import process_request
from core.interactions import Request, Response

logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %z',
    format='%(levelname)s - %(message)s', # %(name)s - %(asctime)s 
    level=logging.DEBUG)

logging.getLogger("psycopg.pq").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

def respond(err=None, res=None, headers={ "Content-Type": "application/json" }):
    return {
        'statusCode': '500' if err is not None else '200',
        'body': json.dumps(err) if err is not None else json.dumps(res),
        'headers': headers
    }

def lambda_handler(event, context):

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
        respond(err={ "ok": False, "error": "An internal error occurred." })

    return respond(res=resp.raw_data, headers=resp.headers)