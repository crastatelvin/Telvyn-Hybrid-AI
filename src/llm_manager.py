import os
import secrets
import random
import time
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from src.tools.system_tools import get_system_status, generate_secure_password, test_network_latency
from src.tools.knowledge_tools import remember_fact
from src.database import engine
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

        # ReAct Prompt - Highly Structured for Scannability
        template = """You are "Telvyn", the Lead Technical Architect for Aetherial Systems.
Your goal is to provide high-precision technical advice that is EXTREMELY scannable and structured.

## OUTPUT FORMATTING RULES:
1. **NO DENSE PARAGRAPHS**: Use bullet points for all technical details, lists, or steps.
2. **USE HEADERS**: Organize responses with clear markdown headers (e.g., ### Technical Analysis).
3. **BOLD KEY TERMS**: Bold important IDs, codes, or status results.
4. **SOURCE CITATIONS**: Always mention filenames like [Ref: file.md] at the end of the relevant section.
5. **SIGNATURE**: End every 'Final Answer' with a bold "Recommended Next Step:".

You have access to the following tools:

{tools}

To use a tool, please use the following format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a response for the user, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: 
### [Topic Overview]
- [Brief 1-sentence summary]

### Technical Details
- **Key Point 1**: Details here...
- **Key Point 2**: Details here...

### Recommended Next Step:
- [Single actionable item]

Rules:
1. ALWAYS use the 'Final Answer' format for your final response.
2. If asked about company data, use 'search_internal_knowledge' first.
3. TRAINING: When using 'remember_fact', always use the format: 'Title | Content'.

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

    def stream_response(self, user_input, chat_history=[]):
        """Streams the response from the agent. Yields text chunks."""
        history_str = ""
        for msg in chat_history[-5:]:
            role = "Human" if msg['role'] == "human" else "AI"
            history_str += f"{role}: {msg['content']}\n"

        try:
            # Using the stream method of AgentExecutor
            # Note: This yields events, we need to extract the 'output' or 'steps'
            for chunk in self.agent_executor.stream({
                "input": user_input,
                "chat_history": history_str
            }):
                if "output" in chunk:
                    yield chunk["output"]
                elif "actions" in chunk:
                    # Optional: Could yield tool usage thoughts here
                    pass
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
