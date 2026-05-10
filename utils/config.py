"""
Centralized Configuration Manager.
Provides hybrid support for both Streamlit Secrets (for cloud deployment)
and local .env variables (for local development).
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables as fallback
load_dotenv()

def get_secret(key: str, default=None) -> str:
    """
    Retrieves a secret with a hybrid fallback mechanism.
    1. Checks Streamlit st.secrets (Streamlit Cloud).
    2. Fallback to os.environ (Local .env).
    3. Returns default if not found.
    """
    try:
        # Check Streamlit secrets first (for cloud deployments)
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # st.secrets throws an exception if accessed outside of a Streamlit run context
        pass
        
    # Fallback to standard environment variables (for local development)
    return os.environ.get(key, default)

def validate_config() -> dict:
    """
    Validates the presence of required configurations.
    Returns a dictionary of boolean statuses for the UI.
    """
    return {
        "api_connected": bool(get_secret("GROQ_API_KEY")),
        "smtp_configured": bool(get_secret("EMAIL_ADDRESS") and get_secret("EMAIL_PASSWORD"))
    }
