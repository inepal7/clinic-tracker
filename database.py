"""Database connection and setup helpers."""
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def connect(db_path):
    """Open a SQLite connection that returns rows addressable by column name."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Create all tables and indexes from schema.sql."""
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
