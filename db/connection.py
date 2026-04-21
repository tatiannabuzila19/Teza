import sqlite3
from contextlib import contextmanager
from config import COFFEE_DB, STRES_DB

@contextmanager
def get_coffee_connection():
    """Context manager for coffee data connection."""
    conn = sqlite3.connect(COFFEE_DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_stres_connection():
    """Context manager for stress/user data connection."""
    conn = sqlite3.connect(STRES_DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
