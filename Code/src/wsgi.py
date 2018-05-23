import sys
from os.path import dirname

sys.path.insert(0, dirname(__file__))

from web_api import app as application
