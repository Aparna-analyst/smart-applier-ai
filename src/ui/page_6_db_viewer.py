import streamlit as st
import pandas as pd
from smart_applier.utils.db_utils import (
    list_profiles,
    get_all_jobs,
    get_all_resumes,
)

@st.cache_data
def fetch_all_data():
    return {
        "profiles": list_profiles(),
        "jobs": get_all_jobs(limit=200),
        "resumes": get_all_resumes(),
    }

def run():
    st.header("🗂️ Database Viewer (Admin Panel)")
    st.write("View all data stored in your Smart Applier database.")

    st.info("⚠️ This panel is READ-ONLY.")

    try:
        data = fetch_all_data()
    except Exception as e:
        st.error(f"Failed loading database: {e}")
        return

    tab1, tab2, tab3 = st.tabs(["👤 Profiles", "💼 Jobs", "📄 Resumes"])

    # PROFILES TAB
    with tab1:
        st.subheader("All Profiles")
        profiles = data["profiles"]
        if not profiles:
            st.info("No profiles found.")
        else:
            st.dataframe(pd.DataFrame(profiles))

    # JOBS TAB
    with tab2:
        st.subheader("All Jobs (Latest First)")
        jobs = data["jobs"]
        if not jobs:
            st.info("No jobs found.")
        else:
            st.dataframe(pd.DataFrame(jobs))

    # RESUMES TAB
    with tab3:
        st.subheader("All Resumes")
        resumes = data["resumes"]
        if not resumes:
            st.info("No resumes found.")
        else:
            st.dataframe(pd.DataFrame(resumes))
