#!/usr/bin/env python

import os
import sys
import logging

from functions import process_request
from core.interactions import Request, Response

logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %z',
    format='%(levelname)s - %(message)s', # %(name)s - %(asctime)s 
    level=logging.DEBUG)

logging.getLogger("psycopg.pq").setLevel(logging.INFO)

request = Request(**os.environ)
if request.headers.get("CONTENT_LENGTH", 0) > 0:
    request.set_data(sys.stdin.read(request.headers.get("CONTENT_LENGTH")))
else:
    logging.error(f"Invalid request from {request.host}")
    resp = Response()
    resp.output({ "ok": False })
    sys.exit()

process_request(request)
