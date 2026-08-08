import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from app.py
from app import app as application

if __name__ == "__main__":
    application.run()