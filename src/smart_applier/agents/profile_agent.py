# src/smart_applier/agents/profile_agent.py
from smart_applier.utils.db_utils import insert_or_update_profile, get_profile, list_profiles

class UserProfileAgent:
    def __init__(self):
        pass

    def save_profile(self, profile_data: dict, user_id: str):
        """
        Save profile into SQLite DB (profiles table).
        """
        insert_or_update_profile(user_id, profile_data)
        # Return a logical URI to the saved profile
        return f"db://profiles/{user_id}"

    def load_profile(self, user_id: str):
        """Load profile from DB"""
        return get_profile(user_id)

    def list_profiles(self):
        """Return list of profiles metadata"""
        return list_profiles()
