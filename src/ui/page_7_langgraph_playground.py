import streamlit as st
import traceback
import pandas as pd

from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.langgraph.workflow import build_master_workflow


# LangGraph Workflows
from smart_applier.langgraph.subworkflows import (
    build_job_scraper_workflow,
    build_resume_workflow,
    build_external_jd_workflow,
    build_skill_gap_graph,
    build_custom_jd_skill_graph    
)


def run():

    st.title("LangGraph Playground")
    st.caption("Debug workflows with automatically loaded DB inputs.")
    st.divider()

    # ------------------------------------------------------
    # AUTO LOAD USER FROM DB
    # ------------------------------------------------------
    profile_agent = UserProfileAgent()
    profiles = profile_agent.list_profiles()

    if not profiles:
        st.error(" No profiles found in DB. Create one first.")
        return

    # Auto-select first user
    first_user = profiles[0]
    user_id = first_user["user_id"]

    st.success(f"Loaded user automatically from DB: **{first_user['name']} ({user_id})**")

    # ------------------------------------------------------
    # Workflow Selection
    # ------------------------------------------------------
    workflows = {
        "Master Full Pipeline (Everything)": build_master_workflow,               # ✅ NEW
        "Job Scraper Full Workflow": build_job_scraper_workflow,
        "Resume Generation Only": build_resume_workflow,
        "External JD → Tailored Resume": build_external_jd_workflow,
        "Skill Gap from Scraped Jobs": build_skill_gap_graph,
        "Skill Gap from Custom JD": build_custom_jd_skill_graph,
    }

    selected = st.selectbox("Choose a Workflow", list(workflows.keys()))
    st.markdown("---")

    # Prepare dynamic input dict
    input_data = {"user_id": user_id}

    # ------------------------------------------------------
    # If workflow needs JD text
    # ------------------------------------------------------
    if selected in ["External JD → Tailored Resume", "Skill Gap from Custom JD"]:
        jd_text = st.text_area("Paste Job Description", height=200)
        input_data["jd_text"] = jd_text

        if not jd_text.strip():
            st.warning("Please enter JD text to run this workflow.")
            st.stop()

    st.markdown("---")

    # ------------------------------------------------------
    # RUN WORKFLOW BUTTON
    # ------------------------------------------------------
    if st.button("▶️ Run Workflow"):
        try:
            st.info("Running workflow… please wait.")

            graph = workflows[selected]()   # Build graph
            result = graph.invoke(input_data)

            st.success("Workflow completed!")

            # -----------------------------------------------
            # SMART OUTPUT (NO RAW JSON ANYMORE)
            # -----------------------------------------------

            if result.get("scraped_jobs"):
                st.subheader("Scraped Jobs")
                st.dataframe(pd.DataFrame(result["scraped_jobs"]).head(10))

            if result.get("matched_jobs"):
                st.subheader("Matched Jobs")
                st.dataframe(pd.DataFrame(result["matched_jobs"]).head(10))

            if result.get("skill_gap_recommendations"):
                st.subheader("Skill Gap Recommendations")
                for skill, resources in result["skill_gap_recommendations"].items():
                    st.markdown(f"### {skill.title()}")
                    for r in resources:
                        st.write(f"- {r}")

            if result.get("resume_pdf_bytes"):
                st.subheader("Generated Resume PDF")
                st.download_button(
                    "Download Resume",
                    data=result["resume_pdf_bytes"],
                    file_name="workflow_resume.pdf",
                    mime="application/pdf"
                )

            if result.get("tailored_resume_pdf_bytes"):
                st.subheader("Tailored Resume PDF")
                st.download_button(
                    "Download Tailored Resume",
                    data=result["tailored_resume_pdf_bytes"],
                    file_name="workflow_tailored_resume.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(" Workflow failed")
            st.text(traceback.format_exc())

    st.markdown("---")
    st.caption("This playground auto-loads DB data for smooth debugging.")
