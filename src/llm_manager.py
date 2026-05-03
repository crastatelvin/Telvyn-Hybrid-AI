import os
import time
import json
import ast
from typing import Annotated, List, Union, TypedDict, Literal
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
from src.tools.research_tools import analyze_competitor, scrape_url
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

# --- AGENT STATE ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    next: str  # Next agent to call
    confidence: float
    thought: str

# --- TELVYN MANAGER PHASE 6 (Multi-Agent Supervisor) ---
class TelvynManager:
    def __init__(self):
        # LLM setup (Groq)
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        
        # Persistence & Knowledge
        self.persist_directory = os.getenv("DB_DIR", "./data/chroma_db")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings) if os.path.exists(self.persist_directory) else None

        # Tools
        self.search_tool = DuckDuckGoSearchRun()
        
        @tool
        def generate_analytics_chart(chart_type: Literal["line", "bar", "radar"], data_json: str, title: str):
            """Generates a visualization chart for the user. 
            data_json should be a list of objects like [{'name': 'A', 'value': 10}, ...]."""
            try:
                # Use ast.literal_eval to handle single quotes or non-standard JSON
                data = ast.literal_eval(data_json)
                return f"CHART_DATA: {json.dumps({'type': chart_type, 'data': data, 'title': title})}"
            except Exception as e:
                return f"Error parsing chart data: {str(e)}. Please provide a valid list of objects."

        self.tools = [
            get_system_status, generate_secure_password, test_network_latency,
            remember_fact, self.search_tool, generate_analytics_chart,
            analyze_competitor, scrape_url
        ]
        
        if self.vector_db:
            @tool
            def search_internal_knowledge(query: str) -> str:
                """Search internal company docs. Use for department-specific intelligence."""
                docs = self.vector_db.similarity_search(query, k=3)
                return "\n\n".join([f"Source: {d.metadata.get('source', 'Unknown')}\nContent: {d.page_content}" for d in docs])
            self.tools.append(search_internal_knowledge)

        # Build Graph
        self._build_graph()

    def _build_graph(self):
        # --- NODES ---
        
        def supervisor_node(state: AgentState):
            """Triage the request to the correct specialist."""
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are the Telvyn Supervisor. Route to: RESEARCH (web search), ANALYST (RAG/Internal), VISUALIZER (Charts), or FINISH."),
                MessagesPlaceholder(variable_name="messages"),
            ])
            # For simplicity, we'll let the agent decide 'next' in its content for now
            # but in a full implementation we'd use function calling to select the next node.
            chain = prompt | self.llm
            response = chain.invoke(state["messages"])
            
            # Triage logic
            content = response.content.upper()
            if "RESEARCH" in content: next_node = "researcher"
            elif "ANALYST" in content: next_node = "analyst"
            elif "VISUALIZER" in content: next_node = "visualizer"
            else: next_node = END
            
            return {"next": next_node, "messages": [response]}

        def researcher_node(state: AgentState):
            """Deep search specialist."""
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are the RESEARCH AGENT. Use tools to analyze market/competitors deeply."),
                MessagesPlaceholder(variable_name="messages"),
            ])
            chain = prompt | self.llm.bind_tools(self.tools)
            response = chain.invoke(state["messages"])
            return {"messages": [response], "next": "supervisor"}

        def analyst_node(state: AgentState):
            """Internal data & RAG specialist."""
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are the CORPORATE ANALYST. Focus on internal knowledge and strategic synthesis."),
                MessagesPlaceholder(variable_name="messages"),
            ])
            chain = prompt | self.llm.bind_tools(self.tools)
            response = chain.invoke(state["messages"])
            return {"messages": [response], "next": "supervisor"}

        # --- GRAPH BUILD ---
        workflow = StateGraph(AgentState)
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("researcher", researcher_node)
        workflow.add_node("analyst", analyst_node)
        
        # Tool execution node
        tool_node = ToolNode(self.tools)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("supervisor")

        # Edges
        def router(state: AgentState):
            last_msg = state["messages"][-1]
            if last_msg.tool_calls: return "tools"
            return state["next"]

        workflow.add_conditional_edges("supervisor", router)
        workflow.add_conditional_edges("researcher", router)
        workflow.add_conditional_edges("analyst", router)
        workflow.add_edge("tools", "supervisor") # Always back to supervisor for triage

        self.app = workflow.compile()

    def stream_response(self, user_input, chat_history=[], session_id="default_session"):
        messages = [HumanMessage(content=msg['content']) if msg['role'] == 'human' else AIMessage(content=msg['content']) for msg in chat_history[-5:]]
        messages.append(HumanMessage(content=user_input))

        try:
            full_response = ""
            seen_ids = set()
            for event in self.app.stream({"messages": messages}, stream_mode="updates"):
                for node, update in event.items():
                    if "messages" in update:
                        for msg in update["messages"]:
                            if msg.id in seen_ids: continue
                            seen_ids.add(msg.id)
                            
                            if isinstance(msg, AIMessage):
                                if msg.tool_calls:
                                    yield f"THOUGHT: Specialist [{node}] is executing {msg.tool_calls[0]['name']}..."
                                elif msg.content:
                                    # Heuristic: only yield if it's actual content from a specialist
                                    if node != "supervisor":
                                        full_response += msg.content
                                        yield msg.content
                    
                    if node == "supervisor" and "next" in update:
                        yield f"THOUGHT: Supervisor routing to {update['next']}..."

            log_token_usage(session_id, len(user_input)//4, len(full_response)//4)
        except Exception as e:
            yield f"Telvyn Intelligence Fault: {str(e)}"

    def get_response(self, user_input, chat_history=[]):
        result = self.app.invoke({"messages": [HumanMessage(content=user_input)]})
        return result["messages"][-1].content
