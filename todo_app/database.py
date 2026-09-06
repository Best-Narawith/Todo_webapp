import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "todo.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        sql = f.read()
    c.executescript(sql)
    conn.commit()
    conn.close()

