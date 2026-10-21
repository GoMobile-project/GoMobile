from app import app
from database import init_db

# Initialize database schema if not present
init_db()

if __name__ == "__main__":
    app.run()
