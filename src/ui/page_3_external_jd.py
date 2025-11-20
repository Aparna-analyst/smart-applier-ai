import streamlit as st
import base64
import os

from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import insert_resume

# LangGraph Workflow
from smart_applier.langgraph.subworkflows import build_external_jd_workflow


def run():
    st.title("External JD Tailoring")
    st.caption("Paste a job description and generate a tailored resume using AI-driven workflow automation.")

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
    # Paste JD
    # -------------------------
    jd_text = st.text_area("Paste Job Description", height=250)

    if not jd_text.strip():
        st.info("Paste a job description to begin.")
        return

    # -------------------------
    # Tailor Resume (LangGraph)
    # -------------------------
    if st.button("Tailor Resume"):
        try:
            with st.spinner("Processing JD & tailoring your resume..."):

                if not os.getenv("GEMINI_API_KEY"):
                    st.error("Missing Gemini API Key. Set GEMINI_API_KEY in environment.")
                    return

                # Build workflow
                graph = build_external_jd_workflow()

                # Invoke workflow with inputs
                state = graph.invoke({
                    "user_id": selected_user_id,
                    "jd_text": jd_text
                })

                # Validate output
                if "resume_pdf_bytes" not in state or not state["resume_pdf_bytes"]:
                    st.error("Workflow didn’t return a resume PDF.")
                    return

                pdf_bytes = state["resume_pdf_bytes"]
                tailored_profile = state.get("tailored_profile", {})

                st.success("Tailored Resume Generated Successfully")

                # -------------------------
                # Download Button
                # -------------------------
                st.download_button(
                    label="Download Tailored Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_user_id}_Tailored_Resume.pdf",
                    mime="application/pdf"
                )

                # -------------------------
                # Inline Preview
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
                except:
                    st.warning("Could not preview PDF inline.")

                # -------------------------
                # Save to DB
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
                    st.error(f"Failed to save tailored resume: {e}")

                # Save to session
                st.session_state["tailored_profile"] = tailored_profile
                st.session_state["tailored_resume"] = pdf_bytes

        except Exception as e:
            st.error(f"Tailoring failed: {e}")
