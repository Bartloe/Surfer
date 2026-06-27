import sqlite3
from pathlib import Path

DB_PATH = Path("surfer.db")

def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Voeg kolommen toe als ze nog niet bestaan
    cur.execute("PRAGMA table_info(taste_profiles)")
    columns = [col[1] for col in cur.fetchall()]
    if "google_api_key" not in columns:
        cur.execute("ALTER TABLE taste_profiles ADD COLUMN google_api_key TEXT")
    if "google_cx" not in columns:
        cur.execute("ALTER TABLE taste_profiles ADD COLUMN google_cx TEXT")

    conn.commit()
    conn.close()
    print("[migration] Kolommen google_api_key en google_cx toegevoegd.")

if __name__ == "__main__":
    upgrade()