import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.database_manager import DatabaseManager
from pymongo.errors import ServerSelectionTimeoutError

def check_db_connection():
    try:
        db = DatabaseManager()
        # Ping the server
        db._client.admin.command('ping')
        return db
    except ServerSelectionTimeoutError:
        return None

def analyze():
    db = check_db_connection()
    if not db:
        print("No database connection available. Skipping analysis.")
        return

if __name__ == "__main__":
    analyze()
