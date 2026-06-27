import sqlite3
from pathlib import Path

DB_DIR = Path("database")
DB_PATH = DB_DIR / "surfer.db"


SCHEMA = """
-- ============================================
-- TABEL: taste_profiles
-- ============================================
CREATE TABLE IF NOT EXISTS taste_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brave_api_key TEXT,
    deepseek_api_key TEXT,
    is_active INTEGER DEFAULT 0
);

-- ============================================
-- TABEL: search_terms
-- ============================================
CREATE TABLE IF NOT EXISTS search_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES taste_profiles(id)
);

-- ============================================
-- TABEL: discoveries (succesvolle resultaten)
-- ============================================
CREATE TABLE IF NOT EXISTS discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT,
    snippet TEXT,
    summary TEXT,
    match_score REAL,
    relevance_score REAL,
    engine TEXT,
    profile_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES taste_profiles(id)
);

-- ============================================
-- TABEL: failed_scrapes (mislukte scrapes)
-- ============================================
CREATE TABLE IF NOT EXISTS failed_scrapes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    reason TEXT,
    engine TEXT,
    profile_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES taste_profiles(id)
);
"""


def init_db():
    print("[init_db] Initialiseren van database...")

    # Zorg dat de map bestaat
    DB_DIR.mkdir(exist_ok=True)

    # Verbinding maken
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Schema uitvoeren
    cur.executescript(SCHEMA)

    conn.commit()
    conn.close()

    print(f"[init_db] Database klaar: {DB_PATH}")


if __name__ == "__main__":
    init_db()
