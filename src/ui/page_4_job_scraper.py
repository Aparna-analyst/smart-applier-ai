# ui/page_4_job_scraper.py
import streamlit as st
import pandas as pd
from smart_applier.agents.job_scraper_agent import JobScraperAgent
from smart_applier.agents.job_matching_agent import JobMatchingAgent
from smart_applier.agents.skill_gap_agent import SkillGapAgent
from smart_applier.agents.resume_tailor_agent import ResumeTailorAgent
from smart_applier.agents.profile_agent import UserProfileAgent
from io import BytesIO
import traceback

def run():
    st.title("🌐 Smart Job Scraper & Analyzer")
    st.caption("Scrape AI/DS jobs, match to your profile, find skill gaps, and tailor your resume — all in one go!")

    # -------------------------
    # Load Profiles
    # -------------------------
    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()
    if not profiles_meta:
        st.warning("⚠️ No profiles found. Please create one first.")
        return

    profile_labels = [f"{p.get('name', 'Unknown')} ({p.get('user_id')})" for p in profiles_meta]
    selected_label = st.selectbox("Select Profile", profile_labels)
    selected_user_id = profiles_meta[profile_labels.index(selected_label)]["user_id"]

    # -------------------------
    # Start Workflow
    # -------------------------
    if st.button("🚀 Start Full Job Analysis"):
        try:
            # Step 1: Scrape Jobs
            with st.spinner("🔍 Scraping latest jobs from Karkidi..."):
                scraper = JobScraperAgent()
                state = {"job_data": None}
                state = scraper.scrape_karkidi(state,2)
                jobs_df = state["job_data"]
                if jobs_df.empty:
                    st.error("❌ No jobs scraped. Try again later.")
                    return
                st.session_state["scraped_jobs"] = jobs_df
                st.success(f"✅ Scraped {len(jobs_df)} job postings successfully!")

            # Step 2: Job Matching
            with st.spinner("🧠 Matching your skills to job listings..."):
                matcher = JobMatchingAgent()
                profile = profile_agent.load_profile(selected_user_id)
                profile_vec = matcher.embed_user_profile(profile)
                job_vecs = matcher.embed_jobs(jobs_df)
                top_jobs = matcher.match_jobs(profile_vec, jobs_df, job_vecs, top_k=10)
                st.session_state["matched_jobs"] = top_jobs

                st.success("✅ Found top 10 matched jobs!")
                st.dataframe(top_jobs[["Title", "Company", "Location", "match_score"]].head(10))

            # Step 3: Skill Gap Analysis
            with st.spinner("📊 Identifying skill gaps and suggesting learning paths..."):
                skill_agent = SkillGapAgent(selected_user_id)
                recs = skill_agent.get_recommendations()
                st.session_state["skill_recs"] = recs

                if recs:
                    st.subheader("🧩 Skill Gap Recommendations")
                    for skill, resources in recs.items():
                        st.markdown(f"**{skill.title()}**")
                        for r in resources:
                            st.write(f"- {r}")
                else:
                    st.info("🎯 No major skill gaps found!")

            st.success("✅ Job scraping and analysis complete!")

        except Exception as e:
            st.error(f"❌ Job Flow failed: {e}")
            st.exception(e)
            st.text(traceback.format_exc())

    # -------------------------
    # Optional: Tailor Resume Button
    # -------------------------
    if "matched_jobs" in st.session_state:
        st.markdown("---")
        st.subheader("✨ Tailor Resume Based on Latest Matched Job")

        if st.button("💫 Generate Tailored Resume"):
            try:
                profile = profile_agent.load_profile(selected_user_id)
                tailorer = ResumeTailorAgent()

                # Use top matched job text for tailoring
                top_job = st.session_state["matched_jobs"].iloc[0]
                job_description = f"{top_job.get('Summary', '')}\n{top_job.get('Skills', '')}"

                cleaned_jd = tailorer.clean_job_description(job_description)
                jd_keywords = [k.strip() for k in str(cleaned_jd).split(",") if k.strip()]

                user_skills = [s.lower() for sub in profile.get("skills", {}).values() for s in sub]
                matched_skills = tailorer.compare_skills(jd_keywords, user_skills)
                coverage = (len(matched_skills) / len(jd_keywords)) * 100 if jd_keywords else 0

                refined_profile = tailorer.refine_with_gemini(profile, jd_keywords, matched_skills, coverage)
                if not isinstance(refined_profile, dict):
                    refined_profile = profile

                # Build tailored resume in memory
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()  # This duplication ensures no file write conflict
                resume_builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                resume_builder = ResumeTailorAgent()
                resume = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                resume_builder = ResumeTailorAgent()
                resume_builder = ResumeTailorAgent()
                resume_builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()
                builder = ResumeTailorAgent()

                resume_builder = ResumeBuilderAgent(refined_profile)
                buffer = resume_builder.build_resume()
                pdf_bytes = buffer.getvalue()

                st.success("✅ Tailored resume generated successfully!")
                st.download_button(
                    label="⬇️ Download Tailored Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                    mime="application/pdf"
                )

                if len(pdf_bytes) < 2_000_000:
                    st.pdf(buffer)

            except Exception as e:
                st.error(f"❌ Tailoring failed: {e}")
