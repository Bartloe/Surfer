import sqlite3
from pathlib import Path

DB_PATH = Path("surfer.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_active_profile():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name
        FROM taste_profiles
        WHERE is_active = 1
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1]
    }

def get_search_terms(profile_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT term FROM search_terms WHERE profile_id = ?", (profile_id,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_discovery_result(url, title, snippet, summary, match_score, relevance_score, engine, profile_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO discoveries
        (url, title, snippet, summary, match_score, relevance_score, engine, profile_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (url, title, snippet, summary, match_score, relevance_score, engine, profile_id))
    conn.commit()
    conn.close()

def save_failed_scrape(url, reason, engine, profile_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO failed_scrapes (url, reason, engine, profile_id)
        VALUES (?, ?, ?, ?)
    """, (url, reason, engine, profile_id))
    conn.commit()
    conn.close()