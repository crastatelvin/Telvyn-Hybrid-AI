import streamlit as st
# Telvyn Version: 1.1.2 - Hybrid Search & Persistence
import os
import json
from datetime import datetime
from src.llm_manager import TelvynManager
from src.ingestor import TelvynIngestor
from src.database import init_db, save_message, get_chat_history
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Telvyn Hybrid AI", page_icon="🧠", layout="wide")

# Database Initialization
init_db()
SESSION_ID = "default_session" # Can be dynamic for multi-user

# Custom CSS for Premium Glassmorphism Look
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .stSidebar {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button {
        border-radius: 8px;
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.025em;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 Telvyn: Hybrid AI Advisor")
st.markdown("---")

# Sidebar for Management
with st.sidebar:
    st.header("🔐 Access Control")
    
    # Get password from Env or Secrets
    stored_password = os.getenv("ADMIN_PASSWORD")
    if not stored_password and "ADMIN_PASSWORD" in st.secrets:
        stored_password = st.secrets["ADMIN_PASSWORD"]
    if not stored_password:
        stored_password = "telvyn_admin" # Default fallback

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        admin_password_input = st.text_input("Admin Password", type="password")
        if admin_password_input == stored_password:
            st.session_state.admin_logged_in = True
            st.rerun()
        elif admin_password_input:
            st.error("Invalid Password")
    else:
        st.success("Admin Access Granted")
        if st.button("🔓 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()
        st.markdown("---")
        st.header("⚙️ System Management")
        
        # File Uploader
        uploaded_files = st.file_uploader("📂 Upload Knowledge (.md)", type=["md"], accept_multiple_files=True)
        if uploaded_files:
            if st.button("💾 Save Uploaded Files"):
                knowledge_dir = os.getenv("KNOWLEDGE_DIR", "./knowledge")
                if not os.path.exists(knowledge_dir):
                    os.makedirs(knowledge_dir)
                
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(knowledge_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                st.success(f"Successfully saved {len(uploaded_files)} files!")
                st.info("Sync below to update Telvyn.")

        st.markdown("---")
        
        if st.button("🔄 Sync Knowledge Base"):
            with st.spinner("Indexing documents..."):
                try:
                    ingestor = TelvynIngestor()
                    ingestor.sync_knowledge()
                    # Re-initialize manager to pick up the new vector store
                    st.session_state.telvyn = TelvynManager()
                    st.success("Knowledge Base Synced!")
                except Exception as e:
                    st.error(f"Sync failed: {e}")
        
    st.markdown("---")
    if st.button("🧹 Clear History"):
        # We could delete from DB here, but for now just clear session
        st.session_state.messages = []
        st.rerun()

    st.info("Telvyn uses local RAG and NVIDIA NIM (Llama 3.1) for inference.")

# Initialize Manager
try:
    if "telvyn" not in st.session_state:
        st.session_state.telvyn = TelvynManager()
except Exception as e:
    st.error(f"Initialization Error: {e}. Check your .env file and Groq API Key.")

# Chat History Management
if "messages" not in st.session_state:
    st.session_state.messages = get_chat_history(SESSION_ID)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask Telvyn anything..."):
    # Add user message to history
    st.session_state.messages.append({"role": "human", "content": prompt})
    with st.chat_message("human"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("ai"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Save user message to DB
            save_message(SESSION_ID, "human", prompt)
            
            # Stream the response
            for chunk in st.session_state.telvyn.stream_response(prompt, st.session_state.messages):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "ai", "content": full_response})
            
            # Save AI message to DB
            save_message(SESSION_ID, "ai", full_response)
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
