import sqlite3
from pathlib import Path

DB_PATH = Path("streamlit_app/my_database.sqlite")

def get_connection():
    """Return a SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # so we can access columns by name
    return conn
