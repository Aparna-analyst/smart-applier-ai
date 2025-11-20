import streamlit as st
import base64
import traceback
import pandas as pd

from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import insert_resume

# LangGraph Workflows
from smart_applier.langgraph.subworkflows import (
    build_job_scraper_workflow
)


def run():
    st.title("Smart Job Scraper & Analyzer")
    st.caption("Scrape → Match → Skill Gap → Tailor Resume (fully automated pipeline)")

    # ------------------------------------------------------
    # Load saved profiles
    # ------------------------------------------------------
    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()

    if not profiles_meta:
        st.warning("No profiles found. Create one first.")
        return

    labels = [f"{p['name']} ({p['user_id']})" for p in profiles_meta]
    selected_label = st.selectbox("Select Profile", labels)
    selected_user_id = profiles_meta[labels.index(selected_label)]["user_id"]

    # ----------------------------------------------------------
    # 1️⃣ RUN ENTIRE PIPELINE (NO SECOND BUTTON NEEDED)
    # ----------------------------------------------------------
    if st.button("Start Full Job Analysis + Tailored Resume"):
        try:
            with st.spinner("Running full AI pipeline… (Scrape → Match → Skills → Resume)"):

                graph = build_job_scraper_workflow()
                result = graph.invoke({"user_id": selected_user_id})

            st.success("Pipeline completed successfully!")

            # ---------------------------------------
            # SCRAPED JOBS
            # ---------------------------------------
            scraped = result.get("scraped_jobs")
            if scraped:
                scraped_df = pd.DataFrame(scraped)
                st.subheader("📌 Scraped Jobs")
                st.dataframe(scraped_df.head(10))
            else:
                st.warning("No scraped jobs returned.")

            # ---------------------------------------
            # MATCHED JOBS
            # ---------------------------------------
            matched = result.get("matched_jobs")
            if matched:
                matched_df = pd.DataFrame(matched)
                st.subheader("🎯 Top Matched Jobs")
                st.dataframe(matched_df.head(10))

                # Save for session use
                st.session_state["matched_jobs"] = matched_df
            else:
                st.warning("Job matching returned no results.")

            # ---------------------------------------
            # SKILL GAP
            # ---------------------------------------
            recs = result.get("skill_gap_recommendations")
            if recs:
                st.subheader("🚧 Skill Gap Recommendations")
                for skill, links in recs.items():
                    st.markdown(f"**{skill.title()}**")
                    for r in links:
                        st.write(f"- {r}")
            else:
                st.warning("No skill gap data returned.")

            # ---------------------------------------
            # TAILORED RESUME
            # ---------------------------------------
            pdf_bytes = (
                result.get("tailored_resume_pdf_bytes") or
                result.get("resume_pdf_bytes")
            )

            if pdf_bytes:
                st.subheader("📄 Tailored Resume Generated")

                # 1️⃣ Download
                st.download_button(
                    label="Download Tailored Resume",
                    data=pdf_bytes,
                    file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                    mime="application/pdf"
                )

                # 2️⃣ Preview
                try:
                    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                    st.markdown(
                        f"""
                        <iframe src="data:application/pdf;base64,{b64_pdf}"
                                width="100%" height="700px"></iframe>
                        """,
                        unsafe_allow_html=True
                    )
                except:
                    st.warning("PDF preview failed.")

                # 3️⃣ Save to DB
                try:
                    insert_resume(
                        user_id=selected_user_id,
                        resume_type="tailored_matched_job",
                        file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                        pdf_blob=pdf_bytes
                    )
                    st.success("Tailored resume saved to the system.")
                except Exception as e:
                    st.error(f"Failed to save resume: {e}")

            else:
                st.error("❌ Tailored resume bytes missing from workflow output.")

        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.text(traceback.format_exc())
