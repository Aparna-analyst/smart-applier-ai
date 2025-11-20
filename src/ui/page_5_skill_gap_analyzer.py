import streamlit as st
import pandas as pd
import traceback

from smart_applier.agents.profile_agent import UserProfileAgent
from smart_applier.langgraph.subworkflows import build_skill_gap_graph


def run():
    st.title("Skill Gap Analyzer")
    st.caption("Find missing skills and receive AI-powered learning recommendations.")

    # ------------------------------------------------------
    # Load Profiles
    # ------------------------------------------------------
    profile_agent = UserProfileAgent()
    profiles_meta = profile_agent.list_profiles()

    if not profiles_meta:
        st.warning("No profiles found. Please create one first.")
        return

    profile_labels = [f"{p['name']} ({p['user_id']})" for p in profiles_meta]
    selected_label = st.selectbox("Select Profile", profile_labels)
    selected_user_id = profiles_meta[profile_labels.index(selected_label)]["user_id"]

    st.markdown("---")

    # ======================================================
    # Analyze Skill Gaps Using Scraped Jobs Workflow ONLY
    # ======================================================
    st.subheader("Analyze Against Latest Scraped Jobs")

    if st.button("Analyze My Matched Jobs"):
        try:
            with st.spinner("Computing skill gap…"):
                graph = build_skill_gap_graph()
                result = graph.invoke({"user_id": selected_user_id})

            recommendations = result.get("skill_gap_recommendations", {})

            if not recommendations:
                st.success("No missing skills — you're well aligned! 🎉")
            else:
                st.subheader("Missing Skills & Learning Resources")
                for skill, links in recommendations.items():
                    st.markdown(f"**{skill.title()}**")
                    for r in links:
                        st.write(f"- {r}")

            st.toast("Skill gap analysis complete ✔️")

        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.text(traceback.format_exc())
