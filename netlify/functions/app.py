import sys
import os

# Insert project root directory into sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database import init_db
import serverless_wsgi
from app import app

# Ensure database tables and initial seed data exist
try:
    init_db()
except Exception as e:
    print(f"Notice during init_db: {e}")

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
