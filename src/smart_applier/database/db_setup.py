# src/smart_applier/database/db_setup.py
import sqlite3
from pathlib import Path
from smart_applier.utils.path_utils import get_data_dirs

def get_db_path() -> Path:
    paths = get_data_dirs()
    db_path = paths["db_path"]
    if db_path is None:
        # fallback (shouldn't happen unless in-memory mode)
        data_root = paths["root"]
        db_path = data_root / "smart_applier.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path

def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()

    # Profiles - store full profile JSON
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

    # Raw scraped jobs
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

    # Top matched jobs: separate table (references scraped_jobs.id)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS top_matched_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        user_id TEXT,
        score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Resumes - PDF stored as BLOB
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
    """
    Initialize DB. If `conn` is provided, create tables there (useful for in-memory).
    Otherwise create/open file-backed DB and initialize tables.
    """
    created_here = False
    if conn is None:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        created_here = True

    create_tables(conn)

    if created_here:
        conn.close()
    print(f"✅ Database initialized at: {get_db_path()}")
