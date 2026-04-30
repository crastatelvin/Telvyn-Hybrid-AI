import os
import secrets
import random
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
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
def generate_secure_password(length_input: str = "24") -> str:
    """Generates a high-entropy technical password for system configurations. 
    Input should be the desired length as a string."""
    try:
        length = int(str(length_input))
    except:
        length = 24
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
def remember_fact(training_input: str) -> str:
    """Saves a new fact to the internal knowledge base. 
    Format your input as: 'Title | Content'"""
    try:
        if "|" in training_input:
            fact_title, fact_content = training_input.split("|", 1)
        else:
            fact_title = "User Fact " + time.strftime("%H%M%S")
            fact_content = training_input
            
        safe_title = "".join([c if c.isalnum() else "_" for c in fact_title.strip().lower()])
        filename = f"trained_fact_{safe_title}.md"
        knowledge_dir = os.getenv("KNOWLEDGE_DIR", "./knowledge")
        
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir)
            
        filepath = os.path.join(knowledge_dir, filename)
        content = f"# Trained Fact: {fact_title.strip()}\n\nDate: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{fact_content.strip()}\n"
        
        with open(filepath, "w") as f:
            f.write(content)
            
        return f"SUCCESS: New fact saved to '{filename}'. IMPORTANT: Tell the user they MUST click 'Sync Knowledge Base' in the sidebar for me to actually learn it."
    except Exception as e:
        return f"ERROR saving fact: {str(e)}"

class TelvynManager:
    def __init__(self):
        # Set up LLM
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        # Consistent path
        self.persist_directory = os.getenv("DB_DIR", "./data/chroma_db")
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
        template = """You are "Telvyn", the Lead Technical Architect for Aetherial Systems.
You have access to the following tools:

{tools}

To use a tool, please use the following format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a response for the user, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]

Rules:
1. ALWAYS use the 'Final Answer' format for your final response.
2. CITATIONS: Mention filenames like [Ref: file.md] if using internal knowledge.
3. SIGNATURE: End every 'Final Answer' with a bold "Recommended Next Step:".
4. TRAINING: When using 'remember_fact', always use the format: 'Title | Content'.

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

    def _initialize_retriever(self):
        try:
            # 1. Vector Store Retriever
            vector_retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
            
            # 2. BM25 Retriever
            data = self.vector_db.get()
            docs = data['documents']
            metadatas = data['metadatas']
            
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
