from typing import Dict, Any, List
import pandas as pd
import numpy as np

from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.agents.job_scraper_agent import JobScraperAgent
from smart_applier.agents.job_matching_agent import JobMatchingAgent
from smart_applier.agents.skill_gap_agent import SkillGapAgent
from smart_applier.agents.resume_tailor_agent import ResumeTailorAgent
from smart_applier.agents.resume_builder_agent import ResumeBuilderAgent


# ======================================================
#  BASE NODES
# ======================================================

def load_profile_node(state):
    agent = UserProfileAgent()
    profile = agent.load_profile(state["user_id"])
    return {"profile": profile}


def scrape_jobs_node(state):
    scraper = JobScraperAgent()
    df = scraper.scrape_karkidi(pages=2)
    return {"scraped_jobs": df.to_dict(orient="records")}


def embed_profile_node(state):
    matcher = JobMatchingAgent()
    vec = matcher.embed_user_profile(state["profile"])
    vec = np.array(vec, dtype="float32")
    return {"profile_vector": vec}


def embed_jobs_node(state):
    matcher = JobMatchingAgent()
    df = pd.DataFrame(state["scraped_jobs"])
    vecs = matcher.embed_jobs(df)
    vecs = np.array(vecs, dtype="float32")
    return {"job_embeddings": vecs}


def match_jobs_node(state):
    matcher = JobMatchingAgent()
    df = pd.DataFrame(state["scraped_jobs"])

    profile_vec = np.array(state["profile_vector"], dtype="float32")
    job_vecs = np.array(state["job_embeddings"], dtype="float32")

    if profile_vec.size == 0 or job_vecs.size == 0:
        raise ValueError("❌ Empty embeddings received — cannot match jobs.")

    matched_df = matcher.match_jobs(
        profile_vec,
        df,
        job_vecs,
        top_k=10,
        user_id=state["user_id"]
    )

    return {"matched_jobs": matched_df.to_dict(orient="records")}


def skill_gap_node(state):
    df = pd.DataFrame(state["scraped_jobs"])
    agent = SkillGapAgent(state["profile"], df)
    recs = agent.get_recommendations()
    return {"skill_gap_recommendations": recs}


def resume_builder_node(state):
    builder = ResumeBuilderAgent(state["profile"])
    buffer = builder.build_resume()
    return {"resume_pdf_bytes": buffer.getvalue()}


def tailor_resume_node(state):
    agent = ResumeTailorAgent()

    if not state["matched_jobs"]:
        raise ValueError("No matched jobs found for tailoring.")

    top_job = pd.DataFrame(state["matched_jobs"]).iloc[0].to_dict()

    pdf_bytes = agent.tailor_profile(
        profile=state["profile"],
        top_job=top_job,
        user_id=state["user_id"]
    )

    return {"tailored_resume_pdf_bytes": pdf_bytes}


# ======================================================
#  EXTERNAL JD WORKFLOW NODES
# ======================================================

def clean_jd_node(state):
    jd_text = state["jd_text"]
    tailorer = ResumeTailorAgent()

    cleaned = tailorer.clean_job_description(jd_text)
    jd_keywords = [k.strip() for k in str(cleaned).split(",") if k.strip()]

    if not jd_keywords:
        jd_keywords = [w for w in jd_text.split() if len(w) > 3]

    return {"jd_keywords": jd_keywords}


def tailor_resume_from_jd_node(state):
    agent = ResumeTailorAgent()
    jd_keywords = state["jd_keywords"]
    profile = state["profile"]

    job_dict = {
        "title": "External JD",
        "skills": ", ".join(jd_keywords),
        "description": ", ".join(jd_keywords)
    }

    pdf_bytes = agent.tailor_profile(
        profile=profile,
        top_job=job_dict,
        user_id=state["user_id"]
    )

    return {
        "resume_pdf_bytes": pdf_bytes,
        "tailored_profile": job_dict
    }


# ======================================================
#  FIXED CUSTOM JD SKILL-GAP NODE
# ======================================================

def jd_skill_gap_node(state):
    jd_text = state["jd_text"]
    profile = state["profile"]
    tailorer = ResumeTailorAgent()

    # Extract keywords
    cleaned = tailorer.clean_job_description(jd_text)
    jd_keywords = [k.strip() for k in str(cleaned).split(",") if k.strip()]

    if not jd_keywords:
        jd_keywords = [w for w in jd_text.split() if len(w) > 3]

    # Convert JD → DataFrame exactly like scraped_jobs format
    df = pd.DataFrame([{
        "skills": ", ".join(jd_keywords),
        "summary": "Custom JD",
        "title": "Custom JD Skill Analysis"
    }])

    # Skill gap computation
    agent = SkillGapAgent(profile, df)
    recs = agent.get_recommendations()

    return {
        "jd_keywords": jd_keywords,
        "missing_skills": list(recs.keys()),
        "skill_gap_recommendations": recs
    }
    
