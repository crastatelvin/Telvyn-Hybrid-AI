import os
import time
from typing import Annotated, List, Union, TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from src.tools.system_tools import get_system_status, generate_secure_password, test_network_latency
from src.tools.knowledge_tools import remember_fact
from src.database import engine, log_token_usage
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLAlchemyCache
from dotenv import load_dotenv

load_dotenv()

# --- CACHING SETUP ---
try:
    set_llm_cache(SQLAlchemyCache(engine))
except Exception as e:
    print(f"Caching initialization failed: {e}")

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

class TelvynManager:
    def __init__(self):
        # Set up LLM with Groq
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
        else:
            self.vector_db = None

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
                docs = self.vector_db.similarity_search(query, k=3)
                return "\n\n".join([f"Source: {d.metadata.get('source', 'Unknown')}\nContent: {d.page_content}" for d in docs])
            
            self.tools.append(search_internal_knowledge)

        # Build LangGraph
        self._build_graph()

    def _build_graph(self):
        # Define the nodes
        def call_model(state: AgentState):
            messages = state['messages']
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are Telvyn, a premium futuristic AI assistant. Be concise, technical, and elegant."),
                MessagesPlaceholder(variable_name="messages"),
            ])
            chain = prompt | self.llm.bind_tools(self.tools)
            response = chain.invoke(messages)
            return {"messages": [response]}

        # Define the tool node
        tool_node = ToolNode(self.tools)

        # Define the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", call_model)
        workflow.add_node("action", tool_node)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        def should_continue(state: AgentState):
            last_message = state['messages'][-1]
            if last_message.tool_calls:
                return "action"
            return END

        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("action", "agent")

        # Compile
        self.app = workflow.compile()

    def stream_response(self, user_input, chat_history=[], session_id="default_session"):
        """Streams the response from the LangGraph agent. Yields thought and text chunks."""
        # Format history for LangGraph
        messages = []
        for msg in chat_history[-5:]:
            if msg['role'] == "human":
                messages.append(HumanMessage(content=msg['content']))
            else:
                messages.append(AIMessage(content=msg['content']))
        
        messages.append(HumanMessage(content=user_input))

        try:
            full_response = ""
            # Using stream to capture events
            for event in self.app.stream({"messages": messages}, stream_mode="updates"):
                for node, update in event.items():
                    if node == "agent":
                        msg = update["messages"][-1]
                        if msg.tool_calls:
                            # Yield thought/action info
                            for tc in msg.tool_calls:
                                yield f"THOUGHT: Executing {tc['name']}..."
                        else:
                            # Final content
                            full_response = msg.content
                            yield full_response
                    elif node == "action":
                        yield "THOUGHT: Tool execution complete. Refining response..."

            # Logging usage
            prompt_tokens = len(str(user_input)) // 4
            completion_tokens = len(full_response) // 4
            log_token_usage(session_id, prompt_tokens, completion_tokens)
            
        except Exception as e:
            yield f"Telvyn is experiencing a technical fault: {str(e)}"

    def get_response(self, user_input, chat_history=[]):
        # Wrapper for non-streaming calls
        messages = [HumanMessage(content=user_input)]
        result = self.app.invoke({"messages": messages})
        return result["messages"][-1].content
