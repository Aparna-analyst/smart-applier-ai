# src/ui/page_4_job_scraper.py
import streamlit as st
from smart_applier.agents.job_scraper_agent import JobScraperAgent
from smart_applier.agents.job_matching_agent import JobMatchingAgent
from smart_applier.agents.skill_gap_agent import SkillGapAgent
from smart_applier.agents.resume_tailor_agent import ResumeTailorAgent
from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import insert_resume
import traceback
import base64

def run():
    st.title(" Smart Job Scraper & Analyzer")
    st.caption("Scrape jobs → Match → Skill Gap → Tailor Resume")

    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()

    if not profiles_meta:
        st.warning(" No profiles found. Create one first.")
        return

    labels = [f"{p['name']} ({p['user_id']})" for p in profiles_meta]
    selected_label = st.selectbox("Select Profile", labels)
    selected_user_id = profiles_meta[labels.index(selected_label)]["user_id"]

    # ---------------------------------------
    #  START FULL JOB ANALYSIS
    # ---------------------------------------
    if st.button(" Start Full Job Analysis"):
        try:
            # -------------------------
            # STEP 1 — SCRAPE JOBS
            # -------------------------
            with st.spinner(" Scraping latest jobs..."):
                scraper = JobScraperAgent()
                jobs_df = scraper.scrape_karkidi(pages=2)

                if jobs_df is None or jobs_df.empty:
                    st.error(" No jobs scraped.")
                    return

                st.success(f" Scraped {len(jobs_df)} jobs successfully!")
                st.dataframe(jobs_df.head(10))

            # -------------------------
            # STEP 2 — JOB MATCHING
            # -------------------------
            with st.spinner(" Matching your profile to jobs..."):
                matcher = JobMatchingAgent()

                profile = profile_agent.load_profile(selected_user_id)
                profile_vec = matcher.embed_user_profile(profile)
                job_vecs = matcher.embed_jobs(jobs_df)

                top_jobs = matcher.match_jobs(
                    profile_vec,
                    jobs_df,
                    job_vecs,
                    top_k=10,
                    user_id=selected_user_id
                )

                st.session_state["matched_jobs"] = top_jobs

                st.success(" Job matching complete!")
                st.dataframe(top_jobs.head(10))

            # -------------------------
            # STEP 3 — SKILL GAP
            # -------------------------
            with st.spinner(" Skill gap analysis..."):
                skill_agent = SkillGapAgent(profile=profile, jobs_df=jobs_df)
                recs = skill_agent.get_recommendations()

                if recs:
                    st.subheader(" Missing Skills & Learning Resources")
                    for skill, resources in recs.items():
                        st.markdown(f"**{skill.title()}**")
                        for r in resources:
                            st.write(f"- {r}")
                else:
                    st.success(" No major skill gaps found!")

        except Exception as e:
            st.error(f"Job Flow failed: {e}")
            st.text(traceback.format_exc())

    # ---------------------------------------
    #  TAILOR RESUME BASED ON MATCHED JOB
    # ---------------------------------------
    if "matched_jobs" in st.session_state:
        st.markdown("---")
        st.subheader(" Tailor Resume Based on Latest Matched Job")

        if st.button(" Generate Tailored Resume"):
            try:
                profile = profile_agent.load_profile(selected_user_id)
                tailorer = ResumeTailorAgent()

                # Top matched job
                top_job = st.session_state["matched_jobs"].iloc[0].to_dict()

                # Build tailored resume and return PDF bytes
                pdf_bytes = tailorer.tailor_profile(
                    profile=profile,
                    top_job=top_job,
                    user_id=selected_user_id
                )

                st.success(" Tailored resume generated!")

                # -------------------------
                # 1️⃣ Download Button
                # -------------------------
                st.download_button(
                    label="Download Tailored Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                    mime="application/pdf"
                )

                # -------------------------
                # 2️⃣ Inline PDF Preview
                # -------------------------
                try:
                    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                    pdf_display = f"""
                        <iframe 
                            src="data:application/pdf;base64,{base64_pdf}" 
                            width="100%" height="700px">
                        </iframe>
                    """
                    st.markdown("### 📄 Tailored Resume Preview")
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"Could not preview PDF inline: {e}")

                # -------------------------
                # 3️⃣ Save to DB
                # -------------------------
                try:
                    insert_resume(
                        user_id=selected_user_id,
                        resume_type="tailored_matched_job",
                        file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                        pdf_blob=pdf_bytes
                    )
                    st.success(" Tailored resume saved to the system.")
                except Exception as e:
                    st.error(f"Failed to save resume: {e}")

            except Exception as e:
                st.error(f"❌ Tailoring failed: {e}")
                st.text(traceback.format_exc())
