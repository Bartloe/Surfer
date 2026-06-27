from .db import get_connection


def add_result(url, title, summary, match_score, relevance_score, search_term, engine, timestamp, taste_profile_id):
    conn = get_connection()
    conn.execute("""
        INSERT INTO results (
            url, title, summary, match_score, relevance_score,
            search_term, engine, timestamp, taste_profile_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url, title, summary, match_score, relevance_score,
        search_term, engine, timestamp, taste_profile_id
    ))
    conn.commit()
    conn.close()


def get_results_for_profile(profile_id: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM results
        WHERE taste_profile_id = ?
        ORDER BY id DESC
    """, (profile_id,)).fetchall()
    conn.close()
    return rows


def delete_results_for_profile(profile_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM results WHERE taste_profile_id = ?", (profile_id,))
    conn.commit()
    conn.close()
