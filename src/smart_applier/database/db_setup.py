# src/smart_applier/database/db_setup.py
import sqlite3
from pathlib import Path
from smart_applier.utils.path_utils import get_data_dirs


def get_db_path() -> Path:
    paths = get_data_dirs()
    db_path = paths["db_path"]
    if db_path is None:
        db_path = paths["root"] / "smart_applier.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols


def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()

    # --- Profiles Table ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        name TEXT,
        email TEXT,
        phone TEXT,
        location TEXT,
        linkedin TEXT,
        github TEXT,
        data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 🔥 Auto-add new column if missing (fix for Streamlit Cloud)
    if not column_exists(cur, "profiles", "data_json"):
        cur.execute("ALTER TABLE profiles ADD COLUMN data_json TEXT")

    # --- Scraped Jobs ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scraped_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        experience TEXT,
        skills TEXT,
        summary TEXT,
        posted_on TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- Top Matched Jobs ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS top_matched_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        user_id TEXT,
        score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- Resumes ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        resume_type TEXT,
        file_name TEXT,
        pdf_blob BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()


def initialize_database(conn: sqlite3.Connection = None):
    created_here = False

    if conn is None:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        created_here = True

    create_tables(conn)

    if created_here:
        conn.close()

    print(f"✅ Database initialized at: {get_db_path()}")
