# jira_utils.py - No-cache version
import os
import json
import streamlit as st
from datetime import datetime

JIRA_JSON_FILE = os.path.join(os.path.dirname(__file__), 'stories.json')

def load_jira_db():
    """Load JIRA stories without caching - always fresh"""
    if not os.path.exists(JIRA_JSON_FILE):
        st.sidebar.warning("⚠️ stories.json not found")
        return {}
    
    try:
        # Always read fresh from disk
        with open(JIRA_JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Show load confirmation in sidebar
        load_time = datetime.now().strftime("%H:%M:%S")
        
        return data
        
    except json.JSONDecodeError as e:
        st.sidebar.error(f"❌ Invalid JSON: {e}")
        return {}
    except Exception as e:
        st.sidebar.error(f"❌ Load error: {e}")
        return {}

# Remove all cache-related functions
def clear_stories_cache():
    """Placeholder - no cache to clear"""
    st.sidebar.info("✅ No cache - always fresh data!")

def get_file_info():
    """Get current file info"""
    if not os.path.exists(JIRA_JSON_FILE):
        return "❌ File not found"
    
    try:
        stat = os.stat(JIRA_JSON_FILE)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        return f"📅 Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n📦 Size: {stat.st_size} bytes"
    except Exception as e:
        return f"❌ Error: {e}"
