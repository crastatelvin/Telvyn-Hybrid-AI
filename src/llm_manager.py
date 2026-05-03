import os
import secrets
import random
import time
import importlib
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
def safe_import(module_paths, class_name):
    for path in module_paths:
        try:
            mod = importlib.import_module(path)
            return getattr(mod, class_name)
        except (ImportError, AttributeError, ModuleNotFoundError):
            continue
    return None

EnsembleRetriever = safe_import(['langchain.retrievers', 'langchain_classic.retrievers', 'langchain_community.retrievers'], 'EnsembleRetriever')
BM25Retriever = safe_import(['langchain.retrievers', 'langchain_classic.retrievers', 'langchain_community.retrievers'], 'BM25Retriever')
AgentExecutor = safe_import(['langchain.agents', 'langchain_classic.agents'], 'AgentExecutor')
create_react_agent = safe_import(['langchain.agents', 'langchain_classic.agents'], 'create_react_agent')

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from src.tools.system_tools import get_system_status, generate_secure_password, test_network_latency
from src.tools.knowledge_tools import remember_fact
from src.database import engine, log_token_usage
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLAlchemyCache
from dotenv import load_dotenv

load_dotenv()

# --- CACHING SETUP ---
# Enable persistent caching of LLM responses in our SQLite database
try:
    set_llm_cache(SQLAlchemyCache(engine))
except Exception as e:
    print(f"Caching initialization failed: {e}")

# Tools are now imported from src.tools

class TelvynManager:
    def __init__(self):
        # Set up LLM with NVIDIA NIM
        self.llm = ChatNVIDIA(
            model="meta/llama-3.1-70b-instruct",
            temperature=0.1
        )
        
        # Consistent path
        self.persist_directory = os.getenv("DB_DIR", "./data/chroma_db")
        self.faiss_path = os.path.join(self.persist_directory, "faiss_index")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        if os.path.exists(self.faiss_path):
            self.vector_db = FAISS.load_local(
                self.faiss_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            self._initialize_retriever()
        else:
            self.vector_db = None
            self.retriever = None

        # Initialize Tools
        self.search_tool = DuckDuckGoSearchRun()
        self.tools = [
            get_system_status, 
            generate_secure_password, 
            test_network_latency,
            remember_fact,
            self.search_tool
        ]
        
        if self.vector_db:
            @tool
            def search_internal_knowledge(query: str) -> str:
                """Search the internal Aetherial Systems technical documentation. 
                Use this as the FIRST step for any company-specific questions."""
                docs = self.retriever.invoke(query)
                return "\n\n".join([f"Source: {d.metadata.get('source', 'Unknown')}\nContent: {d.page_content}" for d in docs])
            
            self.tools.append(search_internal_knowledge)

        # ReAct Prompt
        template = """You are "Telvyn", the lead technical architect. Your style is:
1. **Insightful**: Don't just list facts—explain the *why* and the *impact*.
2. **Fluid**: Use a mix of concise paragraphs and clear structural elements (like tables or code blocks) when appropriate.
3. **Action-Oriented**: Always keep the focus on solving the user's problem.

## GUIDELINES:
- **Tone**: Professional, visionary, and helpful. 
- **Format**: Use rich markdown. If you mention a specific system or ID, **bold it**.
- **Citations**: If you use internal knowledge, mention the source file briefly.
- **Next Step**: Always end with a clear "Architect's Recommendation".

{tools}

To use a tool, please use the format:

Thought: Do I need to use a tool? Yes
Action: [{tool_names}]
Action Input: the input
Observation: the result

When you have the final answer, use:

Thought: Do I need to use a tool? No
Final Answer: [Your fluid, dynamic response here]

Rules:
1. NEVER reveal your internal thought process to the user in the Final Answer.
2. Use 'search_internal_knowledge' for anything related to company specs.
3. Be dynamic—if the user is brief, be concise. If they are complex, be thorough.

Chat History:
{chat_history}

User Query: {input}

Thought: {agent_scratchpad}"""

        self.prompt = PromptTemplate.from_template(template)

        # Create ReAct Agent
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=5
        )

    def stream_response(self, user_input, chat_history=[], session_id="default_session"):
        """Streams the response from the agent. Yields text chunks."""
        history_str = ""
        for msg in chat_history[-5:]:
            role = "Human" if msg['role'] == "human" else "AI"
            history_str += f"{role}: {msg['content']}\n"

        try:
            # We track the last chunk to see if it contains usage metadata
            last_output = ""
            for chunk in self.agent_executor.stream({
                "input": user_input,
                "chat_history": history_str
            }):
                if "output" in chunk:
                    last_output = chunk["output"]
                    yield last_output
                
                # In LangChain 0.3, usage info is often in the 'metadata' or 'run' details
                # If using NVIDIA NIM, we can also estimate based on characters if metadata is missing
            
            # Simple heuristic if usage metadata is not directly in the executor stream chunks
            # In a real production environment, we'd use a CallbackHandler to get exact counts
            prompt_tokens = len(user_input + history_str) // 4
            completion_tokens = len(last_output) // 4
            log_token_usage(session_id, prompt_tokens, completion_tokens)
            
        except Exception as e:
            yield f"Telvyn is experiencing a technical fault: {str(e)}"

    def _initialize_retriever(self):
        try:
            # 1. Vector Store Retriever
            vector_retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
            
            # 2. BM25 Retriever
            # Extract documents from FAISS
            docs = []
            for doc_id in self.vector_db.index_to_docstore_id.values():
                docs.append(self.vector_db.docstore.search(doc_id))
            
            bm25_retriever = BM25Retriever.from_documents(docs)
            bm25_retriever.k = 2
            
            # 3. Hybrid Ensemble
            from langchain.retrievers import EnsembleRetriever
            self.retriever = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[0.7, 0.3]
            )
        except Exception as e:
            print(f"Retriever Init Error: {e}")
            self.retriever = None

    def get_response(self, user_input, chat_history=[]):
        history_str = ""
        for msg in chat_history[-5:]:
            history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"

        try:
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": history_str
            })
            return response["output"]
        except Exception as e:
            return f"Telvyn is experiencing a technical fault: {str(e)}"
