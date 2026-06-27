import os
import importlib
import sqlite3
from src.app.services.db import DB_PATH

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def ensure_migration_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_id TEXT UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def get_applied_migrations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT migration_id FROM migrations")
    rows = cursor.fetchall()

    conn.close()
    return {row[0] for row in rows}


def apply_migration(module_name):
    module = importlib.import_module(f"src.app.database.migrations.{module_name}")
    migration_id = module.run()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO migrations (migration_id) VALUES (?)",
        (migration_id,)
    )

    conn.commit()
    conn.close()

    print(f"[Migratie] Uitgevoerd: {migration_id}")


def run_all():
    ensure_migration_table()
    applied = get_applied_migrations()

    for filename in sorted(os.listdir(MIGRATIONS_DIR)):
        if filename.endswith(".py") and filename[0:3].isdigit():
            module_name = filename[:-3]  # strip .py

            if module_name not in applied:
                apply_migration(module_name)
            else:
                print(f"[Migratie] Overslaan (al uitgevoerd): {module_name}")


if __name__ == "__main__":
    run_all()
