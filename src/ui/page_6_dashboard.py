import streamlit as st
import pandas as pd
import plotly.express as px
import base64

from smart_applier.utils.db_utils import (
    list_profiles,
    get_profile,
    get_all_scraped_jobs,
    get_latest_top_matched,
    list_resumes,
    get_resume_blob
)


def run():

    st.title("Your Smart Applier Dashboard")
    st.caption("A clean overview of your profile, skills, jobs, and progress.")
    st.divider()

    # ------------------------------------------------------
    # LOAD MOST RECENT PROFILE
    # ------------------------------------------------------
    profiles = list_profiles()
    if not profiles:
        st.info("No profile found. Please create your profile first.")
        return

    latest = profiles[0]
    user_id = latest["user_id"]
    profile = get_profile(user_id)
    personal = profile.get("personal", {})

    # ------------------------------------------------------
    # PROFILE CARD
    # ------------------------------------------------------
    st.subheader("Profile Overview")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(
            f"""
            <div style='padding:18px; border-radius:12px; 
                        background:#f7f7f7; border:1px solid #eee;'>
                <h3 style="margin-bottom:5px;">{personal.get("name","")}</h3>
                <p style="margin:0; color:#555;">{personal.get("email","")}</p>
                <p style="margin:0; color:#777;">{personal.get("location","")}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style='padding:18px; border-radius:12px; 
                        background:#f7f7f7; border:1px solid #eee;'>
                <p><b>Phone:</b> {personal.get("phone","")}</p>
                <p><b>GitHub:</b> {personal.get("github","")}</p>
                <p><b>LinkedIn:</b> {personal.get("linkedin","")}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # ======================================================
    # RESUME SECTION
    # ======================================================
    st.subheader("Your Resumes")

    resumes = list_resumes()

    if resumes:

        # Categorize resumes cleanly
        basic_resumes = [r for r in resumes if r["resume_type"] == "generated"]
        tailored_matched = [r for r in resumes if r["resume_type"] == "tailored_matched_job"]
        tailored_external = [r for r in resumes if r["resume_type"] == "tailored"]

        colA, colB, colC = st.columns(3)

        # Reusable block for resume download links
        def render_resume_links(resume_list):
            if not resume_list:
                return "None"

            html = ""
            for r in resume_list:
                blob = get_resume_blob(r["id"])
                if blob:
                    b64 = base64.b64encode(blob).decode()

                    link = f"""
                        <a href='data:application/pdf;base64,{b64}' 
                           download='{r['file_name']}'
                           style='color:#0066cc; text-decoration:none; font-size:15px;'>
                           {r['file_name']}
                        </a><br>
                    """
                    html += link
            return html

        with colA:
            st.markdown("### Basic Resume")
            st.markdown(render_resume_links(basic_resumes), unsafe_allow_html=True)

        with colB:
            st.markdown("### Tailored – Top Matched Job")
            st.markdown(render_resume_links(tailored_matched), unsafe_allow_html=True)

        with colC:
            st.markdown("### Tailored – External JD")
            st.markdown(render_resume_links(tailored_external), unsafe_allow_html=True)

    else:
        st.info("No resumes generated yet.")

    st.divider()

    # ======================================================
    # JOB STATS
    # ======================================================
    scraped = get_all_scraped_jobs(limit=5000)
    matched = get_latest_top_matched(limit=5000)

    colA, colB = st.columns(2)
    colA.metric("Total Scraped Jobs", len(scraped))
    colB.metric("Matched Jobs", len(matched))

    st.divider()

    # ======================================================
    # RECENT MATCHED JOBS
    # ======================================================
    st.subheader("Latest Matched Jobs")
    if matched:
        st.dataframe(pd.DataFrame(matched).head(3))
    else:
        st.info("No matched jobs yet.")

    st.divider()

    # ======================================================
    # SKILL PIE CHART
    # ======================================================
    st.subheader("Skill Breakdown")

    skills = profile.get("skills", {})
    skill_counts = {cat: len(items) for cat, items in skills.items()}

    if skill_counts:
        df_sk = pd.DataFrame({"Category": skill_counts.keys(), "Count": skill_counts.values()})
        fig = px.pie(df_sk, names="Category", values="Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skills found.")

    st.divider()

    # ======================================================
    # PROJECTS SECTION
    # ======================================================
    st.subheader("Projects Overview")

    for proj in profile.get("projects", []):
        st.markdown(
            f"""
            <div style='padding:12px; margin-bottom:10px;
                        border-radius:12px; background:#f7f7f7;
                        border:1px solid #eee;'>
                <h4>{proj.get("title","")}</h4>
                <p><b>Skills:</b> {", ".join(proj.get("skills",[]))}</p>
                <p style="color:#555;">{proj.get("description","")}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # ======================================================
    # QUICK ACTION BUTTONS
    # ======================================================
    st.subheader("Quick Actions")

    colX, colY, colZ = st.columns(3)

    with colX:
        if st.button("Update Profile"):
            st.session_state["page"] = "Create Profile"
            st.rerun()

    with colY:
        if st.button("Generate Resume"):
            st.session_state["page"] = "Resume Builder"
            st.rerun()

    with colZ:
        if st.button("Scrape Jobs"):
            st.session_state["page"] = "Job Scraper Flow"
            st.rerun()
