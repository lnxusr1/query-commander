import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'src', 'querycommander', 'VERSION')) as version_file:
    version = version_file.read().strip()

setup(version=version)