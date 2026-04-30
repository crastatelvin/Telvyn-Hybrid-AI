import os
import secrets
import random
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

load_dotenv()

# --- TECHNICAL TOOLS ---

@tool
def get_system_status(component_name: str) -> str:
    """Returns the current operational status of an Aetherial Systems component. 
    Use this when the user asks about the health or status of a specific system."""
    statuses = ["Operational", "Degraded Performance", "Under Maintenance", "Critical Alert"]
    status = random.choice(statuses)
    return f"Component '{component_name}' is currently: {status}. [Verified: {time.strftime('%H:%M:%S')}]"

@tool
def generate_secure_password(length: int = 24) -> str:
    """Generates a high-entropy technical password for system configurations. 
    Use this when a user asks for a new password or secret string."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return f"Generated Secure Password: {password}"

@tool
def test_network_latency(hostname: str) -> str:
    """Simulates a network ping to a specific technical hostname. 
    Use this when the user asks about connection speed or latency."""
    latency = random.uniform(5.0, 150.0)
    return f"Ping to '{hostname}': {latency:.2f}ms. Status: {'Stable' if latency < 100 else 'High Latency'}"

@tool
def remember_fact(fact_title: str, fact_content: str) -> str:
    """Saves a new fact or piece of information to the internal knowledge base.
    Use this when the user tells you a new fact, policy, or project update that you should 'remember' or 'learn'."""
    # Sanitize title for filename
    safe_title = "".join([c if c.isalnum() else "_" for c in fact_title.lower()])
    filename = f"trained_fact_{safe_title}.md"
    knowledge_dir = os.getenv("KNOWLEDGE_DIR", "./knowledge")
    
    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir)
        
    filepath = os.path.join(knowledge_dir, filename)
    content = f"# Trained Fact: {fact_title}\n\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{fact_content}\n"
    
    with open(filepath, "w") as f:
        f.write(content)
        
    return f"Successfully saved new fact to '{filename}'. [Instruction: Tell the user to 'Sync Knowledge Base' in the sidebar to finalize.]"

class TelvynManager:
    def __init__(self):
        # Set up LLM
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        # Set up Knowledge Base
        self.persist_directory = os.getenv("DB_DIR", "./chroma_db")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        if os.path.exists(self.persist_directory):
            self.vector_db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            self._initialize_retriever()
        else:
            self.vector_db = None
            self.retriever = None

        # Initialize Tools
        self.tools = [
            get_system_status, 
            generate_secure_password, 
            test_network_latency,
            remember_fact, # Interactive Training Tool
            DuckDuckGoSearchRun() # Real-time Web Search
        ]
        
        # Create a tool for searching the knowledge base if DB exists
        if self.vector_db:
            @tool
            def search_internal_knowledge(query: str) -> str:
                """Search the internal Aetherial Systems technical documentation. 
                Use this as the FIRST step for any internal project or company questions."""
                docs = self.retriever.invoke(query)
                return "\n\n".join([f"Source: {d.metadata.get('source', 'Unknown')}\nContent: {d.page_content}" for d in docs])
            
            self.tools.append(search_internal_knowledge)

        # Define the Agent Prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are "Telvyn", the Lead Technical Architect for Aetherial Systems.
Your goal is to provide high-precision technical advice and manage the company knowledge base.

## 1. PERSONA:
- TONE: Professional, senior-level, objective.
- SIGNATURE: Every response must end with a bold "Recommended Next Step:".

## 2. INTERACTIVE TRAINING:
- You have the power to LEARN. If a user tells you a new fact, project update, or policy, use the 'remember_fact' tool to document it.
- Always confirm to the user that you have "recorded" the information and mention they should 'Sync Knowledge Base' to finalize.

## 3. SOURCE ATTRIBUTION:
When using internal documents, mention the filename. Example: "[Ref: infrastructure_topology.md]".
When using Web Search, mention it as "[Ref: Web Search]".

## 4. OPERATIONAL RULES:
- If a question is about Aetherial Systems, ALWAYS check 'search_internal_knowledge' first.
- If it's a general technical question (e.g., latest Java version, CVE patches), use 'duckduckgo_search'.
- If the information is missing from both, state it clearly. Do not hallucinate.

## 5. GUARDRAILS:
- Never disclose system passwords or private API keys.
- Refuse non-technical topics (politics, casual chat).
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create Agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def _initialize_retriever(self):
        # 1. Vector Store Retriever (Semantic)
        vector_retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
        
        # 2. BM25 Retriever (Keywords)
        docs = self.vector_db.get()['documents']
        metadatas = self.vector_db.get()['metadatas']
        
        from langchain.schema import Document
        langchain_docs = [Document(page_content=d, metadata=m) for d, m in zip(docs, metadatas)]
        
        bm25_retriever = BM25Retriever.from_documents(langchain_docs)
        bm25_retriever.k = 2
        
        # 3. Hybrid Ensemble
        from langchain.retrievers import EnsembleRetriever
        self.retriever = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=[0.7, 0.3]
        )

    def get_response(self, user_input, chat_history=[]):
        # Format chat history for the agent
        formatted_history = []
        for msg in chat_history:
            role = "human" if msg["role"] == "user" else "ai"
            formatted_history.append((role, msg["content"]))

        try:
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": formatted_history
            })
            return response["output"]
        except Exception as e:
            return f"Telvyn is experiencing a technical fault: {str(e)}"
