# ui/page_4_job_scraper.py
import streamlit as st
from smart_applier.agents.job_scraper_agent import JobScraperAgent
from smart_applier.agents.job_matching_agent import JobMatchingAgent
from smart_applier.agents.skill_gap_agent import SkillGapAgent
from smart_applier.agents.resume_builder_agent import ResumeBuilderAgent
from smart_applier.agents.resume_tailor_agent import ResumeTailorAgent
from smart_applier.agents.profile_agent import UserProfileAgent
import traceback

def run():
    st.title("🌐 Smart Job Scraper & Analyzer")
    st.caption("Scrape jobs → Match → Skill Gap → Tailor Resume")

    # Load profiles
    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()

    if not profiles_meta:
        st.warning("⚠️ No profiles found. Create one first.")
        return

    profile_labels = [f"{p['name']} ({p['user_id']})" for p in profiles_meta]
    selected_label = st.selectbox("Select Profile", profile_labels)
    selected_user_id = profiles_meta[profile_labels.index(selected_label)]["user_id"]

    # -------------------------
    # Start Job Scraper Flow
    # -------------------------
    if st.button("🚀 Start Full Job Analysis"):
        try:
            # STEP 1: Scrape Jobs
            with st.spinner("🔍 Scraping latest Karkidi jobs..."):
                scraper = JobScraperAgent()
                jobs_df = scraper.scrape_karkidi(2)

                if jobs_df.empty:
                    st.error("❌ No jobs scraped.")
                    return

                st.success(f"✅ Scraped {len(jobs_df)} jobs successfully!")
                st.dataframe(jobs_df.head(10))

            # STEP 2: Job Matching
            with st.spinner("🧠 Matching your profile to jobs..."):
                matcher = JobMatchingAgent()

                profile = profile_agent.load_profile(selected_user_id)
                profile_vec = matcher.embed_user_profile(profile)
                job_vecs = matcher.embed_jobs(jobs_df)

                top_jobs = matcher.match_jobs(profile_vec, jobs_df, job_vecs, top_k=10)

                st.session_state["matched_jobs"] = top_jobs
                st.success("✅ Job matching complete!")
                st.dataframe(top_jobs.head(10))

            # STEP 3: Skill Gap Analysis
            with st.spinner("📊 Skill gap analysis..."):
                skill_agent = SkillGapAgent(selected_user_id)
                recs = skill_agent.get_recommendations()

                if recs:
                    st.subheader("🧠 Missing Skills & Learning Resources")
                    for skill, resources in recs.items():
                        st.markdown(f"**{skill.title()}**")
                        for r in resources:
                            st.write(f"- {r}")
                else:
                    st.success("🎉 No major skill gaps found!")

        except Exception as e:
            st.error(f"❌ Job Flow failed: {e}")
            st.text(traceback.format_exc())

    # -------------------------
    # Tailor Resume
    # -------------------------
    if "matched_jobs" in st.session_state:
        st.markdown("---")
        st.subheader("✨ Tailor Resume Based on Latest Matched Job")

        if st.button("💫 Generate Tailored Resume"):
            try:
                profile = profile_agent.load_profile(selected_user_id)
                tailorer = ResumeTailorAgent()

                # Use top job from matching
                top_job = st.session_state["matched_jobs"].iloc[0]
                job_description = f"{top_job.get('summary', '')}\n{top_job.get('skills', '')}"

                # Extract keywords
                cleaned_jd = tailorer.clean_job_description(job_description)
                jd_keywords = [k.strip() for k in str(cleaned_jd).split(",") if k.strip()]

                # Semantic match
                user_skills = [s.lower() for sub in profile.get("skills", {}).values() for s in sub]
                matched_skills = tailorer.compare_skills(jd_keywords, user_skills)
                coverage = (len(matched_skills) / len(jd_keywords) * 100) if jd_keywords else 0

                # Final refinement
                refined_profile = tailorer.refine_with_gemini(profile, jd_keywords, matched_skills, coverage)

                # Build PDF
                resume_builder = ResumeBuilderAgent(refined_profile)
                buffer = resume_builder.build_resume()
                pdf_data = buffer.getvalue()

                st.success("✅ Tailored resume is ready!")
                st.download_button(
                    label="⬇️ Download Tailored Resume PDF",
                    data=pdf_data,
                    file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"❌ Tailoring failed: {e}")
                st.text(traceback.format_exc())
