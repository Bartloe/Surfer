from .db import get_connection


def get_all_profiles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM taste_profiles ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def get_active_profile():
    conn = get_connection()
    row = conn.execute("SELECT * FROM taste_profiles WHERE is_active = 1").fetchone()
    conn.close()
    return row


def create_profile(name: str, description: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO taste_profiles (name, description) VALUES (?, ?)",
        (name, description)
    )
    conn.commit()
    conn.close()


def set_active_profile(profile_id: int):
    conn = get_connection()
    conn.execute("UPDATE taste_profiles SET is_active = 0")
    conn.execute("UPDATE taste_profiles SET is_active = 1 WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()


def delete_profile(profile_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM taste_profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()
