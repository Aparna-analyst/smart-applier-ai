# src/smart_applier/agents/job_scraper_agent.py
from typing import List, Dict, Any
import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime
from smart_applier.utils.db_utils import bulk_insert_scraped_jobs

class JobScraperAgent:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.base_url = "https://www.karkidi.com/Find-Jobs/{page}/all/India"

    def scrape_karkidi(self, pages: int = 3) -> pd.DataFrame:
        jobs_list: List[Dict[str, Any]] = []

        for page in range(1, pages + 1):
            url = self.base_url.format(page=page)
            print(f"🟢 Scraping page {page}: {url}")

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    print(f"⚠️ Failed to fetch page {page}: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.content, "html.parser")
                job_blocks = soup.find_all("div", class_="ads-details")

                for job in job_blocks:
                    try:
                        title = job.find("h4").get_text(strip=True) if job.find("h4") else ""
                        company_tag = job.find("a", href=lambda x: x and "Employer-Profile" in x)
                        company = company_tag.get_text(strip=True) if company_tag else "Unknown Company"
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
                        print(f"⚠️ Error parsing job block: {e}")
                        continue

                time.sleep(1)

            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                continue

        df_jobs = pd.DataFrame(jobs_list)
        print(f"🟢 Scraper Agent: fetched {len(df_jobs)} jobs total")

        if df_jobs.empty:
            return df_jobs

        # Save to DB and get actual DB IDs
        inserted_ids = bulk_insert_scraped_jobs(jobs_list)
        df_jobs["db_id"] = inserted_ids
        print(f"🟢 Assigned DB IDs to scraped jobs ({len(inserted_ids)} rows)")

        return df_jobs
