# smart_applier/agents/job_scraper_agent.py
from typing import List, Dict, Any
import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
from datetime import datetime
from smart_applier.utils.path_utils import get_data_dirs, ensure_database_exists


class JobScraperAgent:
    """
    Scrapes job listings from Karkidi and stores them in SQLite.
    Works both locally & on Streamlit Cloud.
    """

    def __init__(self):
        paths = get_data_dirs()
        self.use_in_memory = paths["use_in_memory_db"]
        self.db_path = paths["db_path"]

        if not self.use_in_memory:
            ensure_database_exists()

        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.base_url = "https://www.karkidi.com/Find-Jobs/{page}/all/India"

    # -----------------------------
    # DB connection helper
    # -----------------------------
    def _get_connection(self):
        if self.use_in_memory:
            conn = sqlite3.connect(":memory:")
            from smart_applier.database.db_setup import create_tables
            create_tables(conn)
            return conn
        return sqlite3.connect(self.db_path)

    # -----------------------------
    # Main scraper: returns DataFrame
    # -----------------------------
    def scrape_karkidi(self, pages: int = 3) -> pd.DataFrame:
        jobs_list: List[Dict[str, Any]] = []

        for page in range(1, pages + 1):
            url = self.base_url.format(page=page)
            print(f"🟢 Scraping page {page}: {url}")

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    print(f"⚠️ Failed page {page}: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.content, "html.parser")
                job_blocks = soup.find_all("div", class_="ads-details")

                for job in job_blocks:
                    try:
                        title = job.find("h4").get_text(strip=True)
                        company_tag = job.find("a", href=lambda x: x and "Employer-Profile" in x)
                        company = company_tag.get_text(strip=True) if company_tag else ""
                        location = job.find("p").get_text(strip=True) if job.find("p") else ""
                        experience_tag = job.find("p", class_="emp-exp")
                        experience = experience_tag.get_text(strip=True) if experience_tag else ""
                        key_skills_tag = job.find("span", string="Key Skills")
                        skills = key_skills_tag.find_next("p").get_text(strip=True) if key_skills_tag else ""
                        summary_tag = job.find("span", string="Summary")
                        summary = summary_tag.find_next("p").get_text(strip=True) if summary_tag else ""
                        posted_tag = job.find("span", string="Posted On")
                        posted_date = posted_tag.find_next("p").get_text(strip=True) if posted_tag else ""

                        jobs_list.append({
                            "title": title,
                            "company": company,
                            "location": location,
                            "experience": experience,
                            "skills": skills,
                            "summary": summary,
                            "posted_on": posted_date,
                            "scraped_at": datetime.now().isoformat()
                        })
                    except Exception as e:
                        print(f"⚠️ Parse error: {e}")
                        continue

                time.sleep(1)

            except Exception as e:
                print(f"❌ Fetch error: {e}")
                continue

        df_jobs = pd.DataFrame(jobs_list)

        if not df_jobs.empty:
            self._save_to_db(df_jobs)

        return df_jobs

    # -----------------------------
    # Save jobs to DB
    # -----------------------------
    def _save_to_db(self, df_jobs: pd.DataFrame):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
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

        for _, row in df_jobs.iterrows():
            cursor.execute("""
                INSERT INTO scraped_jobs (title, company, location, experience, skills, summary, posted_on)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row["title"],
                row["company"],
                row["location"],
                row["experience"],
                row["skills"],
                row["summary"],
                row["posted_on"],
            ))

        conn.commit()
        conn.close()

    # -----------------------------
    # Retrieve jobs
    # -----------------------------
    def fetch_jobs(self, limit: int = 20) -> pd.DataFrame:
        conn = self._get_connection()
        df = pd.read_sql_query(f"SELECT * FROM scraped_jobs ORDER BY id DESC LIMIT {limit}", conn)
        conn.close()
        return df
