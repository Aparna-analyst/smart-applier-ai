from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
import pandas as pd

from smart_applier.langgraph.nodes import (
    load_profile_node,
    scrape_jobs_node,
    embed_profile_node,
    embed_jobs_node,
    match_jobs_node,
    skill_gap_node,
    resume_builder_node,
    tailor_resume_node
)


# -----------------------------
# State Definition
# -----------------------------
class State(TypedDict, total=False):
    user_id: str
    profile: dict

    scraped_jobs: List[dict]
    profile_vector: List[float]
    job_embeddings: List[List[float]]
    matched_jobs: List[dict]

    skill_gap_recommendations: Dict[str, List[str]]

    resume_pdf_bytes: bytes
    tailored_resume_pdf_bytes: bytes


# -----------------------------
# Build Master Workflow
# -----------------------------
def build_master_workflow():
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
