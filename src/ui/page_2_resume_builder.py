# ui/page_2_resume_builder.py
import streamlit as st
from smart_applier.agents.resume_builder_agent import ResumeBuilderAgent
from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import insert_resume
import base64

def run():
    st.title(" Resume Builder")
    st.caption("Generate an ATS-friendly resume PDF from your saved profile.")

    # -------------------------
    # Load Profiles
    # -------------------------
    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()

    if not profiles_meta:
        st.warning(" No profiles found. Please create one first.")
        return

    profile_labels = [f"{p.get('name', 'Unknown')} ({p.get('user_id')})" for p in profiles_meta]
    selected_label = st.selectbox("Select a saved profile", profile_labels)
    selected_user_id = profiles_meta[profile_labels.index(selected_label)]["user_id"]

    # -------------------------
    # Generate Resume
    # -------------------------
    if st.button(" Build Resume"):
        try:
            with st.spinner("Building your professional resume..."):
                profile = profile_agent.load_profile(selected_user_id)
                if not profile:
                    st.error(" Could not load profile from database.")
                    return

                builder = ResumeBuilderAgent(profile)
                buffer = builder.build_resume()
                pdf_bytes = buffer.getvalue()

                st.success(" Resume generated successfully!")

                # -------------------------
                # 🔽 Download Button
                # -------------------------
                st.download_button(
                    label=" Download Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{selected_user_id}_Resume.pdf",
                    mime="application/pdf",
                )

                # -------------------------
                # 👁️ Inline PDF Preview
                # -------------------------
                try:
                    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700px"></iframe>'
                    st.markdown("### 📄 Resume Preview")
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"Could not preview PDF inline: {e}")

                # -------------------------
                # 💾 SAVE TO DB
                # -------------------------
                try:
                    insert_resume(
                        user_id=selected_user_id,
                        resume_type="generated",
                        file_name=f"{selected_user_id}_Resume.pdf",
                        pdf_blob=pdf_bytes
                    )
                    st.success(" Resume saved to the system.")
                except Exception as e:
                    st.error(f"Could not save resume to database: {e}")

        except Exception as e:
            st.error(f"❌ Error generating resume: {e}")
