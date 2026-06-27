import sqlite3
from src.app.services.db import DB_PATH


def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        ALTER TABLE failed_scrapes
        ADD COLUMN fallback_engine TEXT DEFAULT NULL;
    """)

    conn.commit()
    conn.close()

    return "003_add_search_engine_fallback_fields"
