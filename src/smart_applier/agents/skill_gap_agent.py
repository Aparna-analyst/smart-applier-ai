# smart_applier/agents/skill_gap_agent.py
import os
import pandas as pd
from collections import defaultdict
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import google.generativeai as genai
from smart_applier.utils.path_utils import get_data_dirs, ensure_database_exists


class SkillGapAgent:
    """
    Identifies missing skills by comparing a user's profile against job data
    (session-safe, Streamlit Cloud compatible).
    """

    def __init__(self, profile: dict, jobs_df: pd.DataFrame):
        # -------------------------
        # Environment setup
        # -------------------------
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.use_gemini = bool(self.api_key)

        if self.use_gemini:
            try:
                genai.configure(api_key=self.api_key)
                self.model_name = "gemini-2.0-flash-lite"
            except Exception as e:
                print(f"⚠️ Gemini setup failed: {e}")
                self.use_gemini = False
        else:
            print("⚠️ GEMINI_API_KEY not found — skipping Gemini suggestions.")

        # -------------------------
        # Load profile & jobs
        # -------------------------
        if not profile or not isinstance(profile, dict):
            raise ValueError("❌ Invalid or missing profile.")
        self.profile = profile

        if jobs_df is None or jobs_df.empty:
            raise ValueError("❌ No job data provided to SkillGapAgent.")
        self.jobs_df = jobs_df

        # -------------------------
        # Load user skills
        # -------------------------
        self.user_skills = [
            s.lower().strip()
            for subcat, skills in self.profile.get("skills", {}).items()
            for s in skills if s.strip()
        ]
        if not self.user_skills:
            raise ValueError("⚠️ Profile contains no valid skills.")

        print(f"🧠 Loaded user skills: {len(self.user_skills)} items")

        # -------------------------
        # Initialize semantic model
        # -------------------------
        print("🧩 Loading 'paraphrase-mpnet-base-v2' for semantic analysis...")
        self.model = SentenceTransformer("paraphrase-mpnet-base-v2")
        self.user_embeddings = self.model.encode(self.user_skills, convert_to_tensor=True)

    # -------------------------
    # Skill gap detection
    # -------------------------
    def find_missing_skills(self, job_skills, threshold=0.5):
        """Find job skills not semantically covered by user skills."""
        if not job_skills:
            return []
        job_embeddings = self.model.encode(job_skills, convert_to_tensor=True)
        cosine_scores = util.cos_sim(job_embeddings, self.user_embeddings)
        missing = []
        for i, job_skill in enumerate(job_skills):
            similarity = cosine_scores[i].max().item()
            if similarity < threshold:
                missing.append((job_skill, round(similarity, 3)))
        return missing

    def get_top_missing_skills(self, top_n=5):
        """Collect and rank missing skills across all provided jobs."""
        all_missing_skills = defaultdict(list)
        valid_columns = [col for col in self.jobs_df.columns if "skill" in col.lower()]
        if not valid_columns:
            raise ValueError("❌ No skill-related column found in job data.")
        skill_col = valid_columns[0]

        for _, job in self.jobs_df.iterrows():
            job_skills_text = str(job.get(skill_col, "")).strip()
            if not job_skills_text:
                continue

            job_skills = [
                s.lower().strip()
                for s in job_skills_text.split(",")
                if s.strip()
            ]
            if not job_skills:
                continue

            missing_with_conf = self.find_missing_skills(job_skills)
            for skill, score in missing_with_conf:
                all_missing_skills[skill].append(score)

        if not all_missing_skills:
            return []

        skill_scores = {
            skill: (len(scores), sum(scores) / len(scores))
            for skill, scores in all_missing_skills.items()
        }
        ranked = sorted(skill_scores.items(), key=lambda x: (-x[1][0], x[1][1]))[:top_n]
        top_missing = [skill for skill, _ in ranked]
        return top_missing

    # -------------------------
    # Learning Recommendations
    # -------------------------
    def get_learning_resources(self, skill, n_resources=3):
        """Fetch learning recommendations using Gemini (if available)."""
        if not self.use_gemini:
            # Simple fallback
            return [
                f"Search 'free {skill} course' on Coursera or YouTube.",
                f"Check Kaggle Learn for {skill} tutorials.",
            ]
        try:
            prompt = (
                f"List {n_resources} free, credible online learning resources "
                f"for the skill '{skill}'. Include URLs if available."
            )
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            text = getattr(response, "text", str(response)).strip()
            return [
                line.strip("-• ").strip()
                for line in text.split("\n")
                if line.strip()
            ][:n_resources]
        except Exception as e:
            print(f"⚠️ Gemini resource fetch failed for '{skill}': {e}")
            return []

    def get_recommendations(self, top_n=5):
        """Return dictionary of missing skills + resources."""
        top_missing = self.get_top_missing_skills(top_n=top_n)
        recommendations = {}
        for skill in top_missing:
            recommendations[skill] = self.get_learning_resources(skill)
        return recommendations
