import streamlit as st
import json
import os
import bcrypt
import requests
from jira_utils import load_jira_db

jira_db = load_jira_db()

FASTAPI_HOST = "http://localhost:8000"
USERS_FILE = 'users.json'

# --- Helper functions for user management ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# --- Backend API Callers ---
def get_code_suggestion(prompt):
    resp = requests.post(
        f"{FASTAPI_HOST}/generate-springboot",
        json={"prompt": prompt, "download": False},
        # timeout=120
    )
    resp.raise_for_status()
    return resp.json()["response"]

def chat_with_agent(message):
    resp = requests.post(
        f"{FASTAPI_HOST}/prompt",
        json={"prompt": message},
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["response"]

# --- Style ---
st.set_page_config(page_title='DTDC', page_icon=None)
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        body {background: #f5f7fa;}
        .lloyds-card {background: #fff; border-radius: 18px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.10); padding: 2.5rem 2.5rem 2rem 2.5rem;
        min-width: 350px; max-width: 400px; width: 100%; margin: 2rem 0;}
    </style>
""", unsafe_allow_html=True)

# --- Session state initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'employee_id' not in st.session_state:
    st.session_state.employee_id = ''
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'jira_number' not in st.session_state:
    st.session_state.jira_number = ''
if 'jira_details' not in st.session_state:
    st.session_state.jira_details = None
if 'code_suggestion' not in st.session_state:
    st.session_state.code_suggestion = None
if 'satisfied' not in st.session_state:
    st.session_state.satisfied = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'users' not in st.session_state:
    st.session_state.users = load_users()

# --- Login/Signup Flow ---
if not st.session_state.logged_in:
    if not st.session_state.show_signup:
        st.image('lloyds_logo.png', width=220)
        st.write('Login to your account:')
        with st.form('login_form'):
            employee_id = st.text_input('Employee ID')
            password = st.text_input('Password', type='password')
            submit = st.form_submit_button('Login')
        if submit:
            user = st.session_state.users.get(employee_id)
            if user and check_password(password, user['password_hash']):
                st.session_state.logged_in = True
                st.session_state.employee_id = employee_id
                st.success('Login successful! Redirecting to Home...')
                st.session_state.show_signup = False
                st.rerun()
            else:
                st.error('Invalid Employee ID or Password.')
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("Don't have an account?")
        with col2:
            if st.button('Go to Signup'):
                st.session_state.show_signup = True
                st.rerun()
    else:
        st.image('lloyds_logo.png', width=220)
        st.write('Signup:')
        with st.form('signup_form'):
            employee_id = st.text_input('Employee ID')
            first_name = st.text_input('First Name')
            last_name = st.text_input('Last Name')
            email = st.text_input('Email')
            phone = st.text_input('Phone Number')
            password = st.text_input('Password', type='password')
            submit = st.form_submit_button('Sign Up')
        if submit:
            if employee_id in st.session_state.users:
                st.error('Employee ID already exists.')
            elif any(u['email'] == email for u in st.session_state.users.values()):
                st.error('Email already registered.')
            else:
                st.session_state.users[employee_id] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'password_hash': hash_password(password)
                }
                save_users(st.session_state.users)
                st.success('Signup successful! Please login.')
                st.session_state.show_signup = False
                st.rerun()
        if st.button('Back to Login'):
            st.session_state.show_signup = False
            st.rerun()
else:
    # --- User Home / Code Suggestion Workflow ---
    user = st.session_state.users.get(st.session_state.employee_id, {})
    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    col1, col2, col3 = st.columns([2, 2, 1])
    with col2:
        st.markdown(
            f"<div style='font-weight:600;font-size:1.1rem;padding-top:0.5rem;text-align:center;'>Welcome, {full_name}</div>",
            unsafe_allow_html=True
        )
    with col3:
        if st.button('Logout'):
            st.session_state.logged_in = False
            st.session_state.employee_id = ''
            st.session_state.show_signup = False
            st.rerun()

    st.header('Jira Search & Code Suggestions')

    # Jira Search
    jira_number = st.text_input('Enter Jira Number (e.g. JIRA-101)', value=st.session_state.jira_number)
    search = st.button('Search Jira')
    if search and jira_number:
        search_jira_number = jira_number.strip().upper()
        jira_story = jira_db.get(search_jira_number)
        if jira_story:
            st.session_state.jira_number = search_jira_number
            st.session_state.jira_details = jira_story
            st.session_state.code_suggestion = None
            st.session_state.satisfied = None
            st.session_state.chat_history = []
        else:
            st.session_state.jira_details = None
            st.session_state.code_suggestion = None
            st.warning("Jira number not found in local DB.")

    # Display Jira Details
    if st.session_state.jira_details:
        details = st.session_state.jira_details
        st.subheader('Jira Story Details')
        st.markdown(f"**Story Line:** {details.get('story_line','')}")
        st.markdown(f"**Description:** {details.get('description','')}")
        st.markdown("**Acceptance Criteria:**")
        for c in details.get("acceptance_criteria", []):
            st.markdown(f"- {c}")
        st.markdown(f"**Story Points:** {details.get('story_points','')}")
        refs = details.get("reference_links", [])
        if refs:
            st.markdown("**Reference Links:**")
            for ref in refs:
                st.markdown(f"- [{ref}]({ref})")

        # Generate Code Suggestions - IMPROVED VERSION
        if st.button('Generate Code Suggestions'):
            prompt = (
                f"Jira Number: {st.session_state.jira_number}\n"
                f"Story Line: {details.get('story_line','')}\n"
                f"Description: {details.get('description','')}\n"
                f"Acceptance Criteria: {', '.join(details.get('acceptance_criteria', []))}\n"
                f"Story Points: {details.get('story_points','')}\n"
                f"Reference Links: {', '.join(details.get('reference_links', []))}"
            )
            try:
                with st.spinner("Contacting code agent..."):
                    code = get_code_suggestion(prompt)
                st.session_state.code_suggestion = code
                st.session_state.satisfied = None
            except Exception as e:
                st.session_state.code_suggestion = None
                st.error(f"Failed to get code suggestion: {e}")

        # Show Code Suggestion if Available
        if st.session_state.code_suggestion:
            st.subheader('Code Suggestion')
            st.code(st.session_state.code_suggestion)
            
            # Optional: Clear button
            if st.button('Clear Suggestion'):
                st.session_state.code_suggestion = None
                st.session_state.satisfied = None
                st.rerun()

            # Satisfaction Prompt
            if st.session_state.satisfied is None:
                st.write('Are you satisfied with the code suggestion?')
                col1, col2 = st.columns(2)
                with col1:
                    if st.button('Yes, I am satisfied'):
                        st.session_state.satisfied = True
                        st.success('Great! You can search another Jira or logout.')
                with col2:
                    if st.button('No, I want to chat with AI agent'):
                        st.session_state.satisfied = False
            elif st.session_state.satisfied is False:
                st.subheader('Chat with AI Agent')
                
                # Initialize chat input in session state
                if 'current_message' not in st.session_state:
                    st.session_state.current_message = ''
                
                # Display chat history
                for i, chat in enumerate(st.session_state.chat_history):
                    st.markdown(f"**You:** {chat['user']}")
                    st.markdown(f"**AI:** {chat['ai']}")
                
                # User input stored in session state
                st.session_state.current_message = st.text_input(
                    'Your message:', 
                    value=st.session_state.current_message,
                    key='persistent_chat_input'
                )
                
                # Send button
                if st.button('Send'):
                    if st.session_state.current_message and st.session_state.current_message.strip():
                        message_to_send = st.session_state.current_message
                        st.write(f"Sending: {message_to_send}")  # DEBUG: Remove after testing
                        try:
                            with st.spinner("Getting AI response..."):
                                ai_response = chat_with_agent(message_to_send)
                            st.session_state.chat_history.append({
                                'user': message_to_send, 
                                'ai': ai_response
                            })
                            st.session_state.current_message = ''  # Clear input after sending
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chat agent error: {e}")
                    else:
                        st.warning("Please enter a message before sending.")

