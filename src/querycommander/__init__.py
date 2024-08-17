import os

with open(os.path.join(os.path.dirname(__file__), "VERSION"), "r", encoding="UTF-8") as fp:
    __version__ = fp.read().strip()

VERSION = [int(x) for x in __version__.split(".")]
