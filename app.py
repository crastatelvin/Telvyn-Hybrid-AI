import os
import json
import time
import streamlit as st
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from src.llm_manager import TelvynManager
from src.ingestor import TelvynIngestor

# Setup chat history file path
HISTORY_FILE = "./data/chat_history.json"

def load_all_history():
    if not os.path.exists(HISTORY_FILE):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        # Create empty structure with a default workspace
        with open(HISTORY_FILE, "w") as f:
            json.dump({"Architect Workspace 1": [{"role": "assistant", "content": "Welcome to the Neural Architect Workspace. How can I assist you with technical systems today?"}]}, f)
        return {"Architect Workspace 1": [{"role": "assistant", "content": "Welcome to the Neural Architect Workspace. How can I assist you with technical systems today?"}]}
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            if not data:
                return {"Architect Workspace 1": [{"role": "assistant", "content": "Welcome to the Neural Architect Workspace. How can I assist you with technical systems today?"}]}
            return data
    except Exception:
        return {"Architect Workspace 1": [{"role": "assistant", "content": "Welcome to the Neural Architect Workspace. How can I assist you with technical systems today?"}]}

def save_history(all_history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(all_history, f, indent=2)

def get_session_history(session_name):
    history = load_all_history()
    return history.get(session_name, [])

def append_to_session_history(session_name, role, content):
    history = load_all_history()
    if session_name not in history:
        history[session_name] = []
    history[session_name].append({"role": role, "content": content})
    save_history(history)

def get_all_sessions():
    history = load_all_history()
    return list(history.keys())

# Page Configuration
st.set_page_config(
    page_title="TELVYN - Hybrid AI Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Glassmorphic CSS Styling
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* Global Styles */
        .stApp {
            background: radial-gradient(circle at 50% 0%, #0c0b1a 0%, #050508 100%);
            color: #e2e8f0;
            font-family: 'Outfit', sans-serif;
        }
        
        /* Ultra Smooth Scroll */
        html {
            scroll-behavior: smooth;
        }
        
        /* Header Banner Design */
        .header-container {
            background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.01) 100%);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            transition: border-color 0.3s ease;
        }
        .header-container:hover {
            border-color: rgba(0, 191, 255, 0.2);
        }
        
        /* Status Badges */
        .status-badge {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #10b981;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #10b981;
        }

        .status-badge-inactive {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #ef4444;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        .status-dot-inactive {
            width: 8px;
            height: 8px;
            background-color: #ef4444;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #ef4444;
        }
        
        /* Premium Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #00BFFF 0%, #7B2CBF 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 8px 20px !important;
            font-weight: 600 !important;
            letter-spacing: 0.03em !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(0, 191, 255, 0.1) !important;
            width: 100%;
        }
        
        .stButton>button:hover {
            transform: translateY(-1.5px) !important;
            box-shadow: 0 6px 18px rgba(0, 191, 255, 0.25) !important;
            filter: brightness(1.1);
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #06050b !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04);
        }
        
        /* Card Panel design */
        .glass-card {
            background: rgba(255, 255, 255, 0.015);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            backdrop-filter: blur(8px);
        }
        
        /* Thought step animation container */
        .thought-container {
            background-color: rgba(123, 44, 191, 0.04);
            border-left: 3px solid #7B2CBF;
            border-radius: 4px 12px 12px 4px;
            padding: 12px 16px;
            margin: 12px 0;
            color: #d8b4fe;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            line-height: 1.5;
            animation: pulse-border 2s infinite ease-in-out;
        }
        
        @keyframes pulse-border {
            0% { border-left-color: #7B2CBF; }
            50% { border-left-color: #00BFFF; }
            100% { border-left-color: #7B2CBF; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session states with dict-based access (fixes static typing alerts)
if "session_name" not in st.session_state:
    st.session_state["session_name"] = "Architect Workspace 1"

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

if "telvyn_manager" not in st.session_state:
    with st.spinner("Initializing Telvyn brain context..."):
        st.session_state["telvyn_manager"] = TelvynManager()

# Sidebar Layout (Logically Arranged)
with st.sidebar:
    # Logo / Identity
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 24px; padding: 6px 0;">
            <div style="padding: 10px; background: rgba(0, 191, 255, 0.12); border-radius: 14px; border: 1px solid rgba(0, 191, 255, 0.25);">
                <span style="font-size: 1.8rem; line-height: 1;">🧠</span>
            </div>
            <div>
                <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">
                    TELVYN <span style="color: #00BFFF;">HYBRID</span>
                </h2>
                <p style="margin: 0; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.25em; color: rgba(255, 255, 255, 0.4); font-weight: 700;">
                    Systems Architect
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section 1: Active Conversations
    st.markdown("<p style='font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: rgba(255, 255, 255, 0.35); margin-bottom: 8px;'>Active Workspaces</p>", unsafe_allow_html=True)
    
    sessions = get_all_sessions()
    
    current_session = str(st.session_state["session_name"])
    if current_session not in sessions:
        sessions.insert(0, current_session)
        
    selected_name = st.selectbox(
        label="Select Workspace",
        options=sessions,
        index=sessions.index(current_session),
        label_visibility="collapsed"
    )
    if selected_name != current_session:
        st.session_state["session_name"] = selected_name
        st.rerun()
    
    # Inline Popover to Create a Named Session
    with st.popover("➕ CREATE NEW WORKSPACE", use_container_width=True):
        new_name_input = st.text_input("Workspace Name", placeholder="e.g. Database Scaling")
        if st.button("Confirm Creation", use_container_width=True):
            cleaned_name = new_name_input.strip()
            if cleaned_name:
                # Initialize workspace with system welcome message
                append_to_session_history(cleaned_name, "assistant", f"Workspace '{cleaned_name}' initialized. I am ready to analyze system parameters.")
                st.session_state["session_name"] = cleaned_name
                st.rerun()
            else:
                st.warning("Name cannot be empty")
        
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Section 2: Telemetry Metrics (arranged inside a clean glass card)
    st.markdown("<p style='font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: rgba(255, 255, 255, 0.35); margin-bottom: 8px;'>Telemetry Metrics</p>", unsafe_allow_html=True)
    
    history_msgs = get_session_history(str(st.session_state["session_name"]))
    token_overhead = sum(len(m["content"]) // 4 for m in history_msgs)
    
    st.markdown(
        f"""
        <div class="glass-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 0.65rem; color: rgba(255, 255, 255, 0.4); text-transform: uppercase;">Context Overhead</span>
                <span style="font-size: 0.75rem; font-weight: 700; color: #00BFFF;">{token_overhead:,} tkn</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="font-size: 0.65rem; color: rgba(255, 255, 255, 0.4); text-transform: uppercase;">Inference Speed</span>
                <span style="font-size: 0.75rem; font-weight: 700; color: #a855f7;">75 tokens/s</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Section 3: Admin Governance Panel
    st.markdown("<p style='font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: rgba(255, 255, 255, 0.35); margin-bottom: 8px;'>Admin Governance</p>", unsafe_allow_html=True)
    
    if st.session_state["is_admin"]:
        # Admin is Logged In
        st.markdown(
            """
            <div style="margin-bottom: 12px;">
                <span class="status-badge"><span class="status-dot"></span> Admin Authenticated</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Knowledge Management UI
        with st.expander("📂 Knowledge Base Admin", expanded=True):
            if st.button("🔄 SYNC KNOWLEDGE BASE", use_container_width=True):
                with st.spinner("Rebuilding indexes..."):
                    try:
                        ingestor = TelvynIngestor()
                        ingestor.sync_knowledge()
                        st.session_state["telvyn_manager"] = TelvynManager()
                        st.success("Synchronized successfully!")
                    except Exception as e:
                        st.error(f"Sync failed: {e}")
            
            uploaded_files = st.file_uploader("Upload technical specs (.md)", type=["md"], accept_multiple_files=True)
            if uploaded_files:
                knowledge_dir = os.getenv("KNOWLEDGE_DIR", "./knowledge")
                internal_dir = os.path.join(knowledge_dir, "internal")
                os.makedirs(internal_dir, exist_ok=True)
                
                saved_names = []
                for file in uploaded_files:
                    file_path = os.path.join(internal_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.read())
                    saved_names.append(file.name)
                st.success(f"Saved: {', '.join(saved_names)}")
        
        # Admin Logout
        if st.button("🔒 LOGOUT ADMIN", use_container_width=True):
            st.session_state["is_admin"] = False
            st.success("Logged out")
            time.sleep(0.5)
            st.rerun()
            
    else:
        # Admin is Logged Out
        st.markdown(
            """
            <div style="margin-bottom: 12px;">
                <span class="status-badge-inactive"><span class="status-dot-inactive"></span> User Mode</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        admin_pass_input = st.text_input("Governance Key", type="password", placeholder="Enter Password")
        if st.button("🔓 AUTHORIZE", use_container_width=True):
            env_password = os.getenv("ADMIN_PASSWORD", "telvyn_admin")
            if admin_pass_input == env_password:
                st.session_state["is_admin"] = True
                st.success("Authorized!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Invalid key credentials")

# Main Panel Workspace
st.markdown(
    f"""
    <div class="header-container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
            <div>
                <h1 style="margin: 0; font-size: 1.8rem; font-weight: 800; letter-spacing: -0.02em; color: #ffffff;">{st.session_state["session_name"]}</h1>
                <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: rgba(255, 255, 255, 0.45);">Neural System Architect Link Online</p>
            </div>
            <div style="display: flex; gap: 10px;">
                <span class="status-badge"><span class="status-dot"></span> Groq Llama-3.3</span>
                <span class="status-badge"><span class="status-dot"></span> Hybrid Search</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Render Chat Log
for msg in history_msgs:
    role = "user" if msg["role"] == "human" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])

# User Input operational transmit
user_input = st.chat_input("Transmit parameters or queries to Telvyn...")

if user_input:
    # Render user query
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Append message to persistence
    append_to_session_history(str(st.session_state["session_name"]), "human", user_input)
    
    # Process response in streaming container
    with st.chat_message("assistant"):
        thought_placeholder = st.empty()
        response_placeholder = st.empty()
        
        full_response = ""
        last_thought = ""
        
        # Load chat context history
        history_context = get_session_history(str(st.session_state["session_name"]))[:-1]
        
        manager = st.session_state["telvyn_manager"]
        response_generator = manager.stream_response(
            user_input=user_input,
            chat_history=history_context,
            session_id=str(st.session_state["session_name"])
        )
        
        for chunk in response_generator:
            if chunk.startswith("THOUGHT:"):
                last_thought = chunk.replace("THOUGHT: ", "").strip()
                thought_placeholder.markdown(
                    f"""
                    <div class="thought-container">
                        🔄 <b>Thinking Process:</b> {last_thought}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # Clear thought placeholder to transition smoothly to final text
                thought_placeholder.empty()
                full_response += chunk
                response_placeholder.markdown(full_response)
                
        # Save output to persistence
        if full_response:
            append_to_session_history(str(st.session_state["session_name"]), "ai", full_response)
            
        # Rerun to cleanly update metrics and refresh components
        st.rerun()
