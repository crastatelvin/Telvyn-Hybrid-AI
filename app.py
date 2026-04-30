import streamlit as st
import os
import json
from datetime import datetime
from src.llm_manager import TelvynManager
from src.ingestor import TelvynIngestor
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Telvyn Hybrid AI", page_icon="🧠", layout="wide")

# Persistence Helpers
HISTORY_FILE = "data/chat_history.json"

def save_history(messages):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(messages, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .sidebar .sidebar-content {
        background-image: linear-gradient(#2e7bcf,#2e7bcf);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 Telvyn: Hybrid AI Advisor")
st.markdown("---")

# Sidebar for Management
with st.sidebar:
    st.header("🔐 Access Control")
    admin_password_input = st.text_input("Admin Password", type="password")
    
    # Get password from Env or Secrets
    stored_password = os.getenv("ADMIN_PASSWORD")
    if not stored_password and "ADMIN_PASSWORD" in st.secrets:
        stored_password = st.secrets["ADMIN_PASSWORD"]
    if not stored_password:
        stored_password = "telvyn_admin" # Default fallback
        
    is_admin = admin_password_input == stored_password
    
    if is_admin:
        st.success("Admin Access Granted")
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
    else:
        if admin_password_input:
            st.error("Invalid Password")
        st.info("End-user mode: Chat interface only.")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.rerun()

    st.markdown("---")
    st.info("Telvyn uses local RAG and Groq (Llama 3.3 70B) for inference.")

# Initialize Manager
try:
    if "telvyn" not in st.session_state:
        st.session_state.telvyn = TelvynManager()
except Exception as e:
    st.error(f"Initialization Error: {e}. Check your .env file and Groq API Key.")

# Chat History Management
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

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
        with st.spinner("Telvyn is thinking..."):
            try:
                response = st.session_state.telvyn.get_response(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "ai", "content": response})
                # Save after AI response
                save_history(st.session_state.messages)
            except Exception as e:
                st.error(f"Error generating response: {e}")
