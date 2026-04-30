import streamlit as st
import os
from src.llm_manager import TelvynManager
from src.ingestor import TelvynIngestor
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Telvyn Hybrid AI", page_icon="🧠", layout="wide")

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
    st.header("⚙️ System Management")
    
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
    st.info("Telvyn uses local RAG and Groq (Llama 3.3 70B) for inference.")

# Initialize Manager
try:
    if "telvyn" not in st.session_state:
        st.session_state.telvyn = TelvynManager()
except Exception as e:
    st.error(f"Initialization Error: {e}. Check your .env file and Groq API Key.")

# Chat History Management
if "messages" not in st.session_state:
    st.session_state.messages = []

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
            except Exception as e:
                st.error(f"Error generating response: {e}")
