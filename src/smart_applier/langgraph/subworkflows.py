from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict

from smart_applier.langgraph.nodes import (
    load_profile_node,
    resume_builder_node,
    tailor_resume_node,
    scrape_jobs_node,
    match_jobs_node,
    skill_gap_node,
    embed_profile_node,
    embed_jobs_node,
    clean_jd_node,
    tailor_resume_from_jd_node,
    jd_skill_gap_node,
)


class State(TypedDict, total=False):
    user_id: str
    profile: dict
    jd_text: str
    jd_keywords: List[str]
    scraped_jobs: List[dict]
    matched_jobs: List[dict]
    profile_vector: List[float]
    job_embeddings: List[List[float]]
    skill_gap_recommendations: Dict[str, List[str]]
    resume_pdf_bytes: bytes
    tailored_resume_pdf_bytes: bytes
    tailored_profile: dict


# ------------------------------
# Resume Only Workflow
# ------------------------------
def build_resume_workflow():
    graph = StateGraph(State)
    graph.add_node("load_profile", load_profile_node)
    graph.add_node("resume", resume_builder_node)

    graph.add_edge("load_profile", "resume")
    graph.add_edge("resume", END)
    graph.set_entry_point("load_profile")
    return graph.compile()


# ------------------------------
# Skill Gap Only Workflow
# ------------------------------
def build_skillgap_workflow():
    graph = StateGraph(State)

    graph.add_node("load_profile", load_profile_node)
    graph.add_node("scrape_jobs", scrape_jobs_node)
    graph.add_node("skill_gap", skill_gap_node)

    graph.add_edge("load_profile", "scrape_jobs")
    graph.add_edge("scrape_jobs", "skill_gap")
    graph.add_edge("skill_gap", END)

    graph.set_entry_point("load_profile")
    return graph.compile()


# ------------------------------
# External JD Tailoring Workflow
# ------------------------------
def build_external_jd_workflow():
    graph = StateGraph(State)

    graph.add_node("load_profile", load_profile_node)
    graph.add_node("clean_jd", clean_jd_node)
    graph.add_node("tailor_resume", tailor_resume_from_jd_node)

    graph.add_edge("load_profile", "clean_jd")
    graph.add_edge("clean_jd", "tailor_resume")
    graph.add_edge("tailor_resume", END)

    graph.set_entry_point("load_profile")
    return graph.compile()
# ------------------------------
# Job Scraper + Matching Workflow
# ------------------------------
def build_job_scraper_workflow():
    graph = StateGraph(State)

    graph.add_node("load_profile", load_profile_node)
    graph.add_node("scrape_jobs", scrape_jobs_node)
    graph.add_node("embed_profile", embed_profile_node)
    graph.add_node("embed_jobs", embed_jobs_node)
    graph.add_node("match_jobs", match_jobs_node)
    graph.add_node("skill_gap", skill_gap_node)
    graph.add_node("tailor_resume", tailor_resume_node)
    graph.add_edge("load_profile", "scrape_jobs")
    graph.add_edge("scrape_jobs", "embed_profile")
    graph.add_edge("embed_profile", "embed_jobs")
    graph.add_edge("embed_jobs", "match_jobs")
    graph.add_edge("match_jobs", "skill_gap")
    graph.add_edge("skill_gap", "tailor_resume")
    graph.add_edge("tailor_resume", END)

    graph.set_entry_point("load_profile")
    return graph.compile()
# ------------------------------
# Tailor Resume From Matched Job Workflow
# ------------------------------
def build_tailor_from_matched_workflow():
    graph = StateGraph(State)

    graph.add_node("load_profile", load_profile_node)
    graph.add_node("scrape_jobs", scrape_jobs_node)
    graph.add_node("embed_profile", embed_profile_node)
    graph.add_node("embed_jobs", embed_jobs_node)
    graph.add_node("match_jobs", match_jobs_node)
    graph.add_node("tailor_resume", tailor_resume_node)

    graph.add_edge("load_profile", "scrape_jobs")
    graph.add_edge("scrape_jobs", "embed_profile")
    graph.add_edge("embed_profile", "embed_jobs")
    graph.add_edge("embed_jobs", "match_jobs")
    graph.add_edge("match_jobs", "tailor_resume")
    graph.add_edge("tailor_resume", END)

    graph.set_entry_point("load_profile")
    return graph.compile()
# ------------------------------
# Skill Gap Workflow Graph
# ------------------------------
def build_skill_gap_graph():
    graph = StateGraph(State)

    graph.add_node("load_profile", load_profile_node)
    graph.add_node("scrape_jobs", scrape_jobs_node)
    graph.add_node("skill_gap", skill_gap_node)

    graph.add_edge("load_profile", "scrape_jobs")
    graph.add_edge("scrape_jobs", "skill_gap")
    graph.add_edge("skill_gap", END)

    graph.set_entry_point("load_profile")
    return graph.compile()
# ------------------------------
# Custom JD → Skill Gap Workflow
# ------------------------------
def build_custom_jd_skill_graph():
    graph = StateGraph(State)

    graph.add_node("load_profile", load_profile_node)
    graph.add_node("jd_skill_gap", jd_skill_gap_node)

    graph.add_edge("load_profile", "jd_skill_gap")
    graph.add_edge("jd_skill_gap", END)

    graph.set_entry_point("load_profile")
    return graph.compile()
