import streamlit as st
from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.utils.db_utils import list_profiles, get_profile


def run():
    st.title("Create / Update Your Smart Applier Profile")
    st.caption("Your profile will be saved and auto-filled whenever you come back.")

    profile_agent = UserProfileAgent()

    # ------------------------------------------------------
    # LOAD EXISTING PROFILE (auto-fill fields)
    # ------------------------------------------------------
    stored_profiles = list_profiles()
    existing_profile = None
    user_id = None

    if stored_profiles:
        user_id = stored_profiles[0]["user_id"]
        existing_profile = get_profile(user_id)

    # Graceful fallbacks
    personal = existing_profile.get("personal", {}) if existing_profile else {}
    education_list = existing_profile.get("education", []) if existing_profile else []
    experience_list = existing_profile.get("experience", []) if existing_profile else []
    achievements_list = existing_profile.get("achievements", []) if existing_profile else []
    certificates_list_existing = existing_profile.get("certificates", []) if existing_profile else []
    projects_list_existing = existing_profile.get("projects", []) if existing_profile else []
    skills_existing = existing_profile.get("skills", {}) if existing_profile else {}

    # ------------------------------------------------------
    # PERSONAL DETAILS
    # ------------------------------------------------------
    st.header("Personal Information")
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Full Name", value=personal.get("name", ""))
        email = st.text_input("Email", value=personal.get("email", ""))
        phone = st.text_input("Phone Number", value=personal.get("phone", ""))

    with col2:
        location = st.text_input("Location (City, State)", value=personal.get("location", ""))
        github = st.text_input("GitHub URL", value=personal.get("github", ""))
        linkedin = st.text_input("LinkedIn URL", value=personal.get("linkedin", ""))

    # ------------------------------------------------------
    # EDUCATION
    # ------------------------------------------------------
    st.header("Education")
    education = st.text_area(
        "List your education (one per line):",
        value="\n".join(education_list)
    )

    # ------------------------------------------------------
    # SKILLS
    # ------------------------------------------------------
    st.header("Skills")
    st.info("Organize skills by category — Programming, Tools, ML, Soft Skills, etc.")

    existing_categories = list(skills_existing.keys())
    num_categories = st.number_input(
        "Number of skill categories",
        min_value=1, max_value=10,
        value=len(existing_categories) if existing_categories else 3
    )

    skills_dict = {}
    for i in range(int(num_categories)):
        st.subheader(f"Category {i + 1}")

        default_category = existing_categories[i] if i < len(existing_categories) else ""
        default_skills = ", ".join(skills_existing.get(default_category, [])) if default_category else ""

        category = st.text_input("Category Name", key=f"cat_{i}", value=default_category)
        skills = st.text_input("Skills (comma-separated)", key=f"skills_{i}", value=default_skills)

        if category:
            skills_dict[category] = [s.strip() for s in skills.split(",") if s.strip()]

    # ------------------------------------------------------
    # PROJECTS
    # ------------------------------------------------------
    st.header("Projects")

    num_projects = st.number_input(
        "Number of projects",
        min_value=1, max_value=10,
        value=len(projects_list_existing) if projects_list_existing else 1
    )

    projects_list = []
    for i in range(int(num_projects)):
        st.subheader(f"Project {i + 1}")

        existing = projects_list_existing[i] if i < len(projects_list_existing) else {}

        title = st.text_input("Title", key=f"proj_title_{i}", value=existing.get("title", ""))
        proj_skills = st.text_input("Skills (comma-separated)", key=f"proj_skills_{i}",
                                    value=", ".join(existing.get("skills", [])))
        desc = st.text_area("Description", key=f"proj_desc_{i}",
                            value=existing.get("description", ""))

        if title:
            projects_list.append({
                "title": title,
                "skills": [s.strip() for s in proj_skills.split(",") if s.strip()],
                "description": desc
            })

    # ------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------
    st.header("Experience")
    experience = st.text_area(
        "Describe your relevant experience (one per line)",
        value="\n".join(experience_list)
    )

    # ------------------------------------------------------
    # CERTIFICATES & ACHIEVEMENTS
    # ------------------------------------------------------
    st.header("Certificates & Achievements")

    num_certificates = st.number_input(
        "Number of certificates",
        min_value=0, max_value=10,
        value=len(certificates_list_existing)
    )

    certificates_list = []
    for i in range(int(num_certificates)):
        existing = certificates_list_existing[i] if i < len(certificates_list_existing) else {}

        cert_name = st.text_input("Certificate Name", key=f"cert_name_{i}", value=existing.get("name", ""))
        cert_source = st.text_input("Issued By", key=f"cert_source_{i}", value=existing.get("source", ""))

        if cert_name:
            certificates_list.append({"name": cert_name, "source": cert_source})

    achievements = st.text_area(
        "Achievements (one per line)",
        value="\n".join(achievements_list)
    )

    # ------------------------------------------------------
    # SAVE PROFILE
    # ------------------------------------------------------
    if st.button("Save Profile"):
        if not email:
            st.error("Please enter your email before saving.")
            return

        new_user_id = email.split("@")[0]

        profile_data = {
            "personal": {
                "name": name,
                "email": email,
                "phone": phone,
                "location": location,
                "github": github,
                "linkedin": linkedin,
            },
            "education": [e.strip() for e in education.splitlines() if e.strip()],
            "skills": skills_dict,
            "projects": projects_list,
            "experience": [e.strip() for e in experience.splitlines() if e.strip()],
            "certificates": certificates_list,
            "achievements": [a.strip() for a in achievements.splitlines() if a.strip()],
        }

        try:
            profile_agent.save_profile(profile_data, new_user_id)
            st.session_state["profile_data"] = profile_data

            st.success(f"Profile saved successfully for `{new_user_id}`")

        except Exception as e:
            st.error(f"❌ Failed to save profile: {e}")
