# ui/page_3_external_jd.py
import streamlit as st
import os
import base64

from smart_applier.agents.resume_tailor_agent import ResumeTailorAgent
from smart_applier.agents.resume_builder_agent import ResumeBuilderAgent
from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import insert_resume


def run():
    st.title("External JD Tailoring")
    st.caption("Paste a job description and generate a tailored resume.")

    # -------------------------
    # Load Profiles
    # -------------------------
    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()

    if not profiles_meta:
        st.warning("No profiles found. Please create one first.")
        return

    labels = [f"{p.get('name', 'Unknown')} ({p.get('user_id')})" for p in profiles_meta]
    selected_label = st.selectbox("Select Profile", labels)
    selected_user_id = profiles_meta[labels.index(selected_label)]["user_id"]

    # -------------------------
    # Paste Job Description
    # -------------------------
    jd_text = st.text_area("Paste Job Description", height=250)

    if not jd_text.strip():
        st.info("Paste a job description to begin.")
        return

    # -------------------------
    # Tailor Resume
    # -------------------------
    if st.button("Tailor Resume"):
        try:
            with st.spinner("Analyzing and generating tailored resume..."):
                profile = profile_agent.load_profile(selected_user_id)
                if not profile:
                    st.error("Could not load profile.")
                    return

                if not os.getenv("GEMINI_API_KEY"):
                    st.error("Missing Gemini API Key. Set GEMINI_API_KEY in your environment.")
                    return

                tailorer = ResumeTailorAgent()

                # Step 1: Extract keywords
                cleaned = tailorer.clean_job_description(jd_text)
                jd_keywords = [k.strip() for k in str(cleaned).split(",") if k.strip()]

                # Fallback extraction
                if not jd_keywords:
                    jd_keywords = [w for w in jd_text.split() if len(w) > 3]
                    st.warning("Keyword extraction fallback used.")

                # Step 2: Compare skills
                user_skills = [
                    s.lower()
                    for sub in profile.get("skills", {}).values()
                    for s in sub
                ]
                matched_skills = tailorer.compare_skills(jd_keywords, user_skills)

                coverage = 0
                if jd_keywords:
                    coverage = (len(matched_skills) / len(jd_keywords)) * 100

                # Step 3: Refine profile using Gemini AI
                refined_profile = tailorer.refine_with_gemini(
                    profile, jd_keywords, matched_skills, coverage
                )

                if not isinstance(refined_profile, dict):
                    st.warning("Gemini returned invalid output. Using original profile.")
                    refined_profile = profile

                # Step 4: Build Tailored Resume
                builder = ResumeBuilderAgent(refined_profile)
                buffer = builder.build_resume()
                pdf_bytes = buffer.getvalue()

                st.success("Tailored Resume Generated Successfully")

                # -------------------------
                # 1️⃣ Download Button
                # -------------------------
                st.download_button(
                    label="Download Tailored Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                    mime="application/pdf",
                )

                # -------------------------
                # 2️⃣ Inline Preview
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
                        resume_type="tailored",
                        file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                        pdf_blob=pdf_bytes
                    )
                    st.success("Tailored resume saved to the system.")
                except Exception as e:
                    st.error(f"Could not save tailored resume to database: {e}")

                # Save to session state
                st.session_state["tailored_profile"] = refined_profile
                st.session_state["tailored_resume"] = pdf_bytes

        except Exception as e:
            st.error(f"Tailoring failed: {e}")
