import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ------------------------------------------------------------
# Database Setup
# ------------------------------------------------------------
from smart_applier.database.db_setup import initialize_database
from smart_applier.utils.path_utils import get_data_dirs

paths = get_data_dirs()
db_path = paths["db_path"]

# Ensure database exists
if db_path and not db_path.exists():
    os.makedirs(db_path.parent, exist_ok=True)
    print("Creating SQLite database...")
    initialize_database()

# ------------------------------------------------------------
# Import UI pages
# ------------------------------------------------------------
from ui import (
    page_1_create_profile,
    page_2_resume_builder,
    page_3_external_jd,
    page_4_job_scraper,
    page_5_skill_gap_analyzer,
    page_6_dashboard,
    page_7_langgraph_playground       # ✅ Needed import
)

# ------------------------------------------------------------
# Streamlit Page Config
# ------------------------------------------------------------
st.set_page_config(
    page_title="Nexara AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# Session State
# ------------------------------------------------------------
st.session_state.setdefault("profile_data", None)
st.session_state.setdefault("page", "Dashboard")

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown(
    """
    <div style="text-align:center; margin-bottom: 10px;">
        <h1 style="color:#003366; font-size:75px; margin:0;">Nexara AI</h1>
        <p style="font-size:25px; font-weight:bold; margin-top:5px;">
            A Platform for the Future — build, match, tailor, and upskill with AI.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Sidebar Navigation
# ------------------------------------------------------------
st.sidebar.header("Navigation")

sections = [
    "Dashboard",
    "Create Profile",
    "Resume Builder",
    "External JD Flow",
    "Job Scraper Flow",
    "Skill Gap Analyzer",
    "Langgraph Playground"      # ✅ Fixed spelling
]

selected = st.sidebar.radio(
    "Go to",
    sections,
    index=sections.index(st.session_state["page"])
)

# Sync state
st.session_state["page"] = selected

# ------------------------------------------------------------
# Router
# ------------------------------------------------------------
page_router = {
    "Dashboard": page_6_dashboard.run,
    "Create Profile": page_1_create_profile.run,
    "Resume Builder": page_2_resume_builder.run,
    "External JD Flow": page_3_external_jd.run,
    "Job Scraper Flow": page_4_job_scraper.run,
    "Skill Gap Analyzer": page_5_skill_gap_analyzer.run,
    "Langgraph Playground": page_7_langgraph_playground.run
}

# Render selected page
page_router[st.session_state["page"]]()
