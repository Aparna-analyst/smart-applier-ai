import streamlit as st
import os
from pathlib import Path

# Database setup
from smart_applier.database.db_setup import initialize_database
from smart_applier.utils.path_utils import get_data_dirs

# Ensure database exists on first run
paths = get_data_dirs()
db_path = paths["root"] / "smart_applier.db"

if not db_path.exists():
    os.makedirs(paths["root"], exist_ok=True)
    print("Creating database...")
    initialize_database()

# Import UI pages
from ui import (
    page_1_create_profile,
    page_2_resume_builder,
    page_3_external_jd,
    page_4_job_scraper,
    page_5_skill_gap_analyzer,
    page_6_dashboard
)

# -------------------------
# Streamlit Configuration
# -------------------------
st.set_page_config(
    page_title="Nexara AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# Setup Session State
# -------------------------
if "profile_data" not in st.session_state:
    st.session_state["profile_data"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"


# -------------------------
# App Header
# -------------------------
st.markdown(
    """
    <div style="text-align:center; margin-bottom: 10px;">
        <h1 style="color:#003366; font-size:75px;">Nexara AI</h1>
        <p style="font-size:25px; font-weight:bold;">A Platform for the Future— build, match, tailor, and upskill with AI.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Sidebar Navigation
# -------------------------
st.sidebar.header(" Navigation")

selected = st.sidebar.radio(
    "Choose a section:",
    [
        "Dashboard",
        "Create Profile",
        "Resume Builder",
        "External JD Flow",
        "Job Scraper Flow",
        "Skill Gap Analyzer"
    ],
    index=["Dashboard", "Create Profile", "Resume Builder",
           "External JD Flow", "Job Scraper Flow", "Skill Gap Analyzer"].index(st.session_state["page"])
)

# Keep sidebar & programmatic navigation in sync
st.session_state["page"] = selected

# -------------------------
# Page Routing
# -------------------------
if st.session_state["page"] == "Dashboard":
    page_6_dashboard.run()

elif st.session_state["page"] == "Create Profile":
    page_1_create_profile.run()

elif st.session_state["page"] == "Resume Builder":
    page_2_resume_builder.run()

elif st.session_state["page"] == "External JD Flow":
    page_3_external_jd.run()

elif st.session_state["page"] == "Job Scraper Flow":
    page_4_job_scraper.run()

elif st.session_state["page"] == "Skill Gap Analyzer":
    page_5_skill_gap_analyzer.run()
