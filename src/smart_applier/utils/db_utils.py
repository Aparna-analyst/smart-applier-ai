# smart_applier/utils/db_utils.py
import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
from smart_applier.utils.path_utils import get_data_dirs
from smart_applier.database.db_setup import initialize_database

# -----------------------------
# Row → dict converter
# -----------------------------
def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# -----------------------------
# DB Connection
# -----------------------------
def get_connection():
    paths = get_data_dirs()
    db_path = paths["db_path"]

    # Streamlit Cloud (in-memory mode)
    if paths.get("use_in_memory_db", False):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = dict_factory
        initialize_database(conn)
        return conn

    # Local persistent DB
    if not os.path.exists(db_path):
        initialize_database()

    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    return conn


# -----------------------------
# Profiles
# -----------------------------
def insert_or_update_profile(user_id: str, profile_data: dict):
    conn = get_connection()
    cur = conn.cursor()

    profile_json = json.dumps(profile_data)

    name = profile_data.get("personal", {}).get("name", "")
    email = profile_data.get("personal", {}).get("email", "")

    cur.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
    exists = cur.fetchone()

    if exists:
        cur.execute("""
            UPDATE profiles
            SET name=?, email=?, profile_json=?
            WHERE user_id=?
        """, (name, email, profile_json, user_id))
    else:
        cur.execute("""
            INSERT INTO profiles (user_id, name, email, profile_json)
            VALUES (?, ?, ?, ?)
        """, (user_id, name, email, profile_json))

    conn.commit()
    conn.close()


def get_profile(user_id: str) -> Optional[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT profile_json FROM profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row["profile_json"])


def list_profiles() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, created_at FROM profiles ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------
# Scraped Jobs
# -----------------------------
def bulk_insert_jobs(jobs: List[Dict[str, Any]]):
    conn = get_connection()
    cur = conn.cursor()

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

    conn.commit()
    conn.close()


def get_all_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scraped_jobs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------
# Top Matched Jobs
# -----------------------------
def insert_top_matched(job_id: int, score: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO top_matched_jobs (job_id, score)
        VALUES (?, ?)
    """, (job_id, score))

    conn.commit()
    conn.close()


def get_latest_top_matched(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT j.*, t.score
        FROM top_matched_jobs t
        JOIN scraped_jobs j ON j.id = t.job_id
        ORDER BY t.id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------
# Resumes
# -----------------------------
def insert_resume(user_id: str, resume_type: str, file_path: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO resumes (user_id, resume_type, file_path)
        VALUES (?, ?, ?)
    """, (user_id, resume_type, file_path))

    conn.commit()
    conn.close()


def get_all_resumes() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM resumes ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
