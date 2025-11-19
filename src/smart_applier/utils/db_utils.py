# src/smart_applier/utils/db_utils.py
import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
from smart_applier.utils.path_utils import get_data_dirs
from smart_applier.database.db_setup import initialize_database

# -----------------------------
# Row factory → return dicts
# -----------------------------
def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

# -----------------------------
# DB Connection Helper
# -----------------------------
def get_connection(in_memory: bool = False) -> sqlite3.Connection:
    paths = get_data_dirs()
    db_path = paths["db_path"]

    if in_memory:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = dict_factory
        initialize_database(conn)
        return conn

    if db_path is None:
        raise RuntimeError("db_path is not configured (USE_IN_MEMORY_DB=1?)")

    first_time = not db_path.exists()
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory

    if first_time:
        initialize_database(conn)

    return conn

# -----------------------------
#  PROFILES
# -----------------------------
def insert_or_update_profile(user_id: str, profile_data: dict):
    conn = get_connection()
    cur = conn.cursor()

    profile_json = json.dumps(profile_data)
    name = profile_data.get("personal", {}).get("name", "")
    email = profile_data.get("personal", {}).get("email", "")
    phone = profile_data.get("personal", {}).get("phone", "")
    location = profile_data.get("personal", {}).get("location", "")
    linkedin = profile_data.get("personal", {}).get("linkedin", "")
    github = profile_data.get("personal", {}).get("github", "")

    cur.execute("SELECT id FROM profiles WHERE user_id=?", (user_id,))
    if cur.fetchone():
        cur.execute("""
            UPDATE profiles
            SET name=?, email=?, phone=?, location=?, linkedin=?, github=?, data_json=?
            WHERE user_id=?
        """, (name, email, phone, location, linkedin, github, profile_json, user_id))
    else:
        cur.execute("""
            INSERT INTO profiles (user_id, name, email, phone, location, linkedin, github, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, phone, location, linkedin, github, profile_json))

    conn.commit()
    conn.close()


def get_profile(user_id: str) -> Optional[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT data_json FROM profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()

    return json.loads(row["data_json"]) if row else None


def list_profiles():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email,data_json, created_at FROM profiles ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

# Compatibility
def get_all_profiles():
    return list_profiles()


# -----------------------------
# SCRAPED JOBS
# -----------------------------
def bulk_insert_scraped_jobs(jobs: List[Dict[str, Any]]) -> List[int]:
    """
    Insert jobs and return DB IDs in the SAME ORDER.
    This ensures no NaN in db_id.
    """
    if not jobs:
        return []

    conn = get_connection()
    cur = conn.cursor()

    inserted_ids = []

    for job in jobs:
        cur.execute("""
            INSERT INTO scraped_jobs (title, company, location, experience, skills, summary, posted_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("title") or job.get("Title"),
            job.get("company") or job.get("Company"),
            job.get("location") or job.get("Location"),
            job.get("experience") or job.get("Experience"),
            job.get("skills") or job.get("Skills"),
            job.get("summary") or job.get("Summary"),
            job.get("posted_on") or job.get("Posted On"),
        ))

        inserted_ids.append(cur.lastrowid)

    conn.commit()
    conn.close()

    return inserted_ids


def get_all_scraped_jobs(limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scraped_jobs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------
#  TOP MATCHED JOBS (SEPARATE TABLE)
# -----------------------------
def insert_top_matched(job_id: int, user_id: str, score: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO top_matched_jobs (job_id, user_id, score)
        VALUES (?, ?, ?)
    """, (job_id, user_id, score))
    conn.commit()
    conn.close()


def get_latest_top_matched(limit: int = 50):
    """
    Join top_matched_jobs with scraped_jobs cleanly.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.id AS match_id,
            t.job_id,
            t.user_id,
            t.score,
            t.created_at AS matched_at,
            s.title,
            s.company,
            s.location,
            s.experience,
            s.skills,
            s.summary,
            s.posted_on
        FROM top_matched_jobs t
        LEFT JOIN scraped_jobs s ON s.id = t.job_id
        ORDER BY t.id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------
#  RESUMES (PDF as BLOB)
# -----------------------------
def insert_resume(user_id: str, resume_type: str, file_name: str, pdf_blob: bytes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO resumes (user_id, resume_type, file_name, pdf_blob)
        VALUES (?, ?, ?, ?)
    """, (user_id, resume_type, file_name, sqlite3.Binary(pdf_blob)))
    conn.commit()
    conn.close()


def list_resumes(limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, resume_type, file_name, created_at FROM resumes ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_resume_blob(resume_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT pdf_blob FROM resumes WHERE id=?", (resume_id,))
    row = cur.fetchone()
    conn.close()
    return row["pdf_blob"] if row else None
# -----------------------------
# Compatibility exports for UI
# -----------------------------
def get_all_profiles():
    return list_profiles()

def get_all_scraped_jobs_for_ui(limit: int = 100):
    return get_all_scraped_jobs(limit)

def get_all_resumes(limit: int = 100):
    return list_resumes(limit)
