# src/smart_applier/agents/resume_tailor_agent.py
import os
import re
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import google.generativeai as genai
from smart_applier.utils.path_utils import get_data_dirs
from smart_applier.agents.resume_builder_agent import ResumeBuilderAgent
from smart_applier.utils.db_utils import insert_resume, get_all_scraped_jobs

class ResumeTailorAgent:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in environment.")
        genai.configure(api_key=api_key)

        self.gemini_model = genai.GenerativeModel("models/gemini-2.0-flash-lite")
        self.model = SentenceTransformer(model_name)

    def clean_job_description(self, job_description: str):
        prompt = f"""
        Extract only the relevant 'skills', 'qualifications', and 'technical requirements'
        from this job description. Return them as a concise comma-separated list.
        ---
        {job_description}
        """
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini JD cleaning failed: {e}")
            return job_description

    def compare_skills(self, jd_keywords, user_skills, threshold=0.45):
        if not jd_keywords or not user_skills:
            return []

        jd_vecs = self.model.encode(jd_keywords, convert_to_tensor=True)
        user_vecs = self.model.encode(user_skills, convert_to_tensor=True)
        cosine = util.cos_sim(jd_vecs, user_vecs)

        matched = set()
        for i, jd_skill in enumerate(jd_keywords):
            if cosine[i].max().item() >= threshold:
                matched.add(jd_skill.lower())

        return list(matched)

    def refine_with_gemini(self, profile, jd_keywords, matched_skills, coverage_score):
        prompt = f"""
        You are a professional resume optimizer.
        Refine user's full profile clearly and return only clean JSON.

        USER PROFILE:
        {json.dumps(profile, indent=2)}

        JOB KEYWORDS:
        {', '.join(jd_keywords)}

        MATCHED SKILLS:
        {', '.join(matched_skills)}

        COVERAGE SCORE: {coverage_score:.2f}
        """

        try:
            response = self.gemini_model.generate_content(prompt)
            text = response.text.strip()

            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return profile

        except Exception as e:
            print(f"⚠️ Gemini refinement failed: {e}")
            return profile

    def tailor_profile(self, profile: dict, top_job=None, user_id: str = ""):
        """
        Full pipeline: clean JD → extract keywords → refine profile → build resume PDF → save PDF
        RETURNS: pdf_bytes (NOT dict)
        """

        # --------------------------------
        # 1. Get job description
        # --------------------------------
        if top_job is None:
            scraped = get_all_scraped_jobs(limit=1)
            if scraped:
                top_job = scraped[0]
            else:
                raise FileNotFoundError("No job available for tailoring.")

        summary_text = top_job.get("summary", "") or ""
        skills_text = top_job.get("skills", "") or ""
        job_description = f"{summary_text}\n{skills_text}".strip()

        # --------------------------------
        # 2. Extract & compare skills
        # --------------------------------
        cleaned_jd = self.clean_job_description(job_description)
        jd_keywords = [kw.strip() for kw in cleaned_jd.split(",") if kw.strip()]

        user_skills = [
            s.lower() for sub in profile.get("skills", {}).values() for s in sub
        ]

        matched_skills = self.compare_skills(jd_keywords, user_skills)

        coverage_score = (len(matched_skills) / len(jd_keywords) * 100) if jd_keywords else 0

        # --------------------------------
        # 3. Refine profile with Gemini
        # --------------------------------
        tailored_profile = self.refine_with_gemini(
            profile, jd_keywords, matched_skills, coverage_score
        )

        # Normalize fields if needed
        if isinstance(tailored_profile.get("experience"), str):
            tailored_profile["experience"] = [{
                "title": "Experience",
                "description": tailored_profile["experience"]
            }]

        if isinstance(tailored_profile.get("projects"), str):
            tailored_profile["projects"] = [{
                "title": "Project",
                "description": tailored_profile["projects"]
            }]

        # --------------------------------
        # 4. Build tailored resume PDF
        # --------------------------------
        builder = ResumeBuilderAgent(tailored_profile)
        buffer = builder.build_resume()
        pdf_bytes = buffer.getvalue()

        file_name = f"{user_id}_Tailored_Resume.pdf"

        # --------------------------------
        # 5. Save PDF to DB
        # --------------------------------
        try:
            insert_resume(
                user_id=user_id,
                resume_type="tailored",
                file_name=file_name,
                pdf_blob=pdf_bytes
            )
        except Exception as e:
            print(f"⚠️ Could not save tailored resume to DB: {e}")

        # --------------------------------
        # 6. RETURN PDF BYTES
        # --------------------------------
        return pdf_bytes
