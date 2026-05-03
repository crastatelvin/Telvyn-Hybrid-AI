import streamlit as st
# Telvyn Version: 1.1.2 - Hybrid Search & Persistence
import os
import json
from datetime import datetime
from src.llm_manager import TelvynManager
from src.ingestor import TelvynIngestor
from src.database import init_db, save_message, get_chat_history, get_total_tokens
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Telvyn Hybrid AI", page_icon="🧠", layout="wide")

# Database Initialization
init_db()
SESSION_ID = "default_session" # Can be dynamic for multi-user

# Enhanced UI/UX with 3D Background and Glassmorphism
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
    .main {
        background: transparent !important;
        color: #f8fafc;
    }
    #three-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
    }
    .stChatMessage {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .stSidebar {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .token-counter {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    <canvas id="three-canvas"></canvas>
    <script>
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('three-canvas'), alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);

    const geometry = new THREE.TorusKnotGeometry(10, 3, 100, 16);
    const material = new THREE.MeshNormalMaterial({ wireframe: true });
    const torusKnot = new THREE.Mesh(geometry, material);
    scene.add(torusKnot);

    camera.position.z = 30;

    function animate() {
        requestAnimationFrame(animate);
        torusKnot.rotation.x += 0.01;
        torusKnot.rotation.y += 0.01;
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    </script>
    """, unsafe_allow_html=True)

st.title("🧠 Telvyn: Technical Architect")
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
    st.header("📊 Usage Telemetry")
    total_tokens = get_total_tokens(SESSION_ID)
    st.markdown(f"""
        <div class="token-counter">
            Total Tokens: {total_tokens:,}
        </div>
    """, unsafe_allow_html=True)

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
            for chunk in st.session_state.telvyn.stream_response(prompt, st.session_state.messages, SESSION_ID):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "ai", "content": full_response})
            
            # Save AI message to DB
            save_message(SESSION_ID, "ai", full_response)
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
