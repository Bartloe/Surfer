#src/app/database/migrations/005_add_user_status.py

import sqlite3
from pathlib import Path

DB_PATH = Path("surfer.db")

def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE discoveries ADD COLUMN user_status TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE failed_scrapes ADD COLUMN user_status TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()
    print("Migratie 005: user_status toegevoegd.")

if __name__ == "__main__":
    upgrade()