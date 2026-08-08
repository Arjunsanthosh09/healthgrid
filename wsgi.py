import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the root app.py module
import app as app_module

# Get the Flask application instance
application = app_module.app