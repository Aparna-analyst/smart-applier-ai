import streamlit as st
from smart_applier.agents.skill_gap_agent import SkillGapAgent
from smart_applier.agents.resume_tailor_agent import ResumeTailorAgent
from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import get_latest_top_matched, get_all_jobs
import traceback
import pandas as pd
import os

def run():
    st.title("📊 Skill Gap Analyzer")
    st.caption("Identify missing skills and get AI-powered learning recommendations.")

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

    profile = profile_agent.load_profile(selected_user_id)

    # -------------------------
    # Analyze Top Matched Jobs
    # -------------------------
    st.markdown("---")
    st.subheader("📈 Analyze Against Top Matched Jobs")

    if st.button("🔍 Analyze My Matched Jobs"):
        try:
            with st.spinner("Fetching matched jobs..."):

                # Prefer saved matched jobs
                jobs = get_latest_top_matched(limit=20)

                # Fallback to all jobs if database empty
                if not jobs:
                    jobs = get_all_jobs(limit=20)

                if not jobs:
                    st.error("❌ No job data available in the database.")
                    return

                jobs_df = pd.DataFrame(jobs)

            with st.spinner("Analyzing skill gaps..."):
                agent = SkillGapAgent(profile, jobs_df)
                recs = agent.get_recommendations()

            if not recs:
                st.success("🎯 No missing skills — you're well-aligned!")
            else:
                st.subheader("🚀 Missing Skills & Learning Recommendations")
                for skill, resources in recs.items():
                    st.markdown(f"**🧠 {skill.title()}**")
                    for r in resources:
                        st.write(f"- {r}")

            st.toast("✅ Skill gap analysis complete!", icon="✨")

        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")
            st.text(traceback.format_exc())

    # -------------------------
    # Analyze Custom JD
    # -------------------------
    st.markdown("---")
    st.subheader("🧩 Analyze Custom Role or Job Description")

    jd_text = st.text_area(
        "Paste job description here", 
        height=250, 
        placeholder="Paste a JD from LinkedIn, Naukri, Karkidi, etc."
    )

    if jd_text.strip() and st.button("🧠 Analyze Custom JD"):
        try:
            tailorer = ResumeTailorAgent()

            st.info("Step 1️⃣ Extracting key JD skills...")
            cleaned = tailorer.clean_job_description(jd_text)
            jd_keywords = [k.strip() for k in str(cleaned).split(",") if k.strip()]

            if not jd_keywords:
                jd_keywords = [w.strip() for w in jd_text.split() if len(w) > 3]
                st.warning("⚠️ No structured skills found — fallback extraction applied.")

            st.info("Step 2️⃣ Matching JD skills with your profile...")
            user_skills = [
                s.lower() 
                for sub in profile.get("skills", {}).values() 
                for s in sub
            ]

            matched = tailorer.compare_skills(jd_keywords, user_skills)
            coverage = (len(matched) / len(jd_keywords) * 100) if jd_keywords else 0
            st.success(f"🎯 Skill Coverage: {coverage:.1f}%")

            missing_skills = [k for k in jd_keywords if k.lower() not in matched]

            if missing_skills:
                st.warning(f"🚧 Missing: {', '.join(missing_skills[:10])} ...")

                # Create fake job dataframe
                fake_jobs_df = pd.DataFrame([{
                    "skills": ", ".join(missing_skills)
                }])

                skill_agent = SkillGapAgent(profile, fake_jobs_df)

                st.subheader("📚 Learning Resources")
                for skill in missing_skills:
                    resources = skill_agent.get_learning_resources(skill)
                    st.markdown(f"**{skill.title()}**")
                    for r in resources:
                        st.write(f"- {r}")

            else:
                st.success("✨ You match all required skills for this JD!")

            st.toast("📈 JD Analysis Completed!", icon="✔️")

        except Exception as e:
            st.error(f"❌ Custom JD Analysis Failed: {e}")
            st.text(traceback.format_exc())
