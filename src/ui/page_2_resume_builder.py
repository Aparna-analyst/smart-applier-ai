import streamlit as st
import base64

from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import insert_resume

# LangGraph resume workflow
from smart_applier.langgraph.subworkflows import build_resume_workflow


def run():
    st.title("Resume Builder")
    st.caption("Generate an ATS-friendly resume PDF from your saved profile using AI-driven automation.")

    # -------------------------
    # Load Profiles
    # -------------------------
    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()

    if not profiles_meta:
        st.warning("No profiles found. Please create one first.")
        return

    profile_labels = [f"{p.get('name', 'Unknown')} ({p.get('user_id')})" for p in profiles_meta]
    selected_label = st.selectbox("Select a saved profile", profile_labels)
    selected_user_id = profiles_meta[profile_labels.index(selected_label)]["user_id"]

    # -------------------------
    # Generate Resume via LangGraph
    # -------------------------
    if st.button("Build Resume"):
        try:
            with st.spinner("Building your resume... please wait."):

                # Run resume-only workflow
                graph = build_resume_workflow()
                state = graph.invoke({"user_id": selected_user_id})

                if "resume_pdf_bytes" not in state or not state["resume_pdf_bytes"]:
                    st.error("Failed to generate resume.")
                    return

                pdf_bytes = state["resume_pdf_bytes"]
                st.success("Resume generated successfully!")

                # -------------------------
                # 🔽 Download Button
                # -------------------------
                st.download_button(
                    label="Download Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_user_id}_Resume.pdf",
                    mime="application/pdf",
                )

                # -------------------------
                # 👁️ Inline Preview
                # -------------------------
                try:
                    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                    pdf_display = f"""
                        <iframe 
                            src="data:application/pdf;base64,{base64_pdf}" 
                            width="100%" height="700px">
                        </iframe>
                    """
                    st.markdown("### 📄 Resume Preview")
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"Could not preview PDF inline: {e}")

                # -------------------------
                # 💾 Save to Database
                # -------------------------
                try:
                    insert_resume(
                        user_id=selected_user_id,
                        resume_type="generated",
                        file_name=f"{selected_user_id}_Resume.pdf",
                        pdf_blob=pdf_bytes
                    )
                    st.success("Resume saved to the system.")
                except Exception as e:
                    st.error(f"Could not save resume to database: {e}")

        except Exception as e:
            st.error(f"❌ Error generating resume: {e}")
