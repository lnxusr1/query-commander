#!/usr/bin/env python

import os
import sys
import logging

from functions import process_request
from core.interactions import Request, Response
from core.helpers import get_page_content

logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %z',
    format='%(levelname)s - %(message)s', # %(name)s - %(asctime)s 
    level=logging.DEBUG)

logging.getLogger("psycopg.pq").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

import start
start.as_cgi()