# jira_utils.py
import os
import json
import streamlit as st

JIRA_JSON_FILE = os.path.join(os.path.dirname(__file__), 'stories.json')

@st.cache_data
def load_jira_db():
    if not os.path.exists(JIRA_JSON_FILE):
        return {}
    with open(JIRA_JSON_FILE, 'r') as f:
        return json.load(f)
