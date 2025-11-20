# src/smart_applier/agents/job_matching_agent.py

from pathlib import Path
import pandas as pd
import numpy as np
import string
import faiss
from sentence_transformers import SentenceTransformer

from smart_applier.utils.path_utils import get_data_dirs
from smart_applier.utils.db_utils import insert_top_matched


class JobMatchingAgent:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # SentenceTransformer for embeddings
        self.model = SentenceTransformer(model_name)

        paths = get_data_dirs()
        self.profiles_dir = paths["profiles"]
        self.jobs_dir = paths["jobs"]

    # ---------------------------------------------------
    # TEXT CLEANING
    # ---------------------------------------------------
    @staticmethod
    def preprocess_text(text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return " ".join(text.split())

    # ---------------------------------------------------
    # USER PROFILE → VECTOR
    # ---------------------------------------------------
    def embed_user_profile(self, profile: dict):
        # collect skills
        skills_text = " ".join(
            " ".join(skill_list)
            for skill_list in profile.get("skills", {}).values()
        )

        # projects
        projects_text = " ".join(
            f"{p.get('title','')} {p.get('description','')}"
            for p in profile.get("projects", [])
        )

        # achievements
        achievements_text = " ".join(profile.get("achievements", []))

        combined = " ".join([skills_text, projects_text, achievements_text])
        combined = self.preprocess_text(combined)

        # FIX — ensure float32
        return self.model.encode(combined, convert_to_numpy=True).astype("float32")

    # ---------------------------------------------------
    # JOBS TEXT → VECTOR
    # ---------------------------------------------------
    def embed_jobs(self, jobs_df: pd.DataFrame):
        job_texts = []

        for _, row in jobs_df.iterrows():
            text = (
                row.get("skills")
                or row.get("summary")
                or ""
            )
            job_texts.append(self.preprocess_text(str(text)))

        # FIX — ensure float32 embeddings
        return self.model.encode(job_texts, convert_to_numpy=True).astype("float32")

    # ---------------------------------------------------
    # FAISS INDEX
    # ---------------------------------------------------
    def build_faiss_index(self, job_embeddings: np.ndarray):
        job_embeddings = job_embeddings.astype("float32")  # *** important ***

        d = job_embeddings.shape[1]
        index = faiss.IndexFlatIP(d)

        faiss.normalize_L2(job_embeddings)
        index.add(job_embeddings)
        return index

    # ---------------------------------------------------
    # MAIN MATCHING LOGIC
    # ---------------------------------------------------
    def match_jobs(
        self,
        profile_vector: np.ndarray,
        jobs_df: pd.DataFrame,
        job_embeddings: np.ndarray,
        top_k=10,
        user_id: str = None
    ):

        if job_embeddings.shape[0] == 0:
            raise ValueError("❌ No job embeddings available.")

        # FIX — ensure float32 everywhere
        profile_vector = profile_vector.astype("float32")
        job_embeddings = job_embeddings.astype("float32")

        # normalize profile vector
        faiss.normalize_L2(profile_vector.reshape(1, -1))

        index = self.build_faiss_index(job_embeddings)
        D, I = index.search(profile_vector.reshape(1, -1), top_k)

        matched = jobs_df.iloc[I[0]].copy().reset_index(drop=True)
        matched["match_score"] = D[0].round(4)

        # SAVE MATCHES FOR DASHBOARD
        if "db_id" in jobs_df.columns:
            for rank, idx in enumerate(I[0]):
                try:
                    db_id = int(jobs_df.iloc[idx]["db_id"])
                    score = float(D[0][rank])
                    insert_top_matched(job_id=db_id, user_id=user_id, score=score)
                except Exception as e:
                    print("⚠️ Failed to save top match:", e)
        else:
            print("⚠️ WARNING: db_id column missing in jobs_df. Top matches not saved.")

        return matched
