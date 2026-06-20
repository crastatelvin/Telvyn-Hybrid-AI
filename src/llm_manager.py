import os
import json
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from src.tools.system_tools import get_system_status, generate_secure_password, test_network_latency
from src.tools.knowledge_tools import remember_fact

load_dotenv()

class TelvynManager:
    def __init__(self):
        # LLM setup (Groq)
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        
        # Persistence & Knowledge
        self.persist_directory = os.getenv("DB_DIR", "./data/chroma_db")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize ChromaDB vector database
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            try:
                self.vector_db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
            except Exception as e:
                print(f"Error loading ChromaDB: {e}")
                self.vector_db = None
        else:
            self.vector_db = None

        # Tools
        self.web_search_tool = DuckDuckGoSearchRun()
        
        # Define Hybrid Search tool
        @tool
        def search_internal_knowledge(query: str) -> str:
            """Search internal company docs using hybrid (vector similarity + BM25 keyword) search.
            Use this tool to find company-specific details, guidelines, policies, specs, or user-submitted facts."""
            # 1. Semantic search
            vector_results = []
            if self.vector_db:
                try:
                    vector_results = self.vector_db.similarity_search(query, k=3)
                except Exception as e:
                    print(f"Vector search failed: {e}")
            
            # 2. BM25 keyword search
            bm25_results = []
            bm25_docs_path = os.path.join(self.persist_directory, "bm25_docs.json")
            if os.path.exists(bm25_docs_path):
                try:
                    with open(bm25_docs_path, "r", encoding="utf-8") as f:
                        raw_docs = json.load(f)
                    if raw_docs:
                        tokenized_corpus = [doc["page_content"].lower().split() for doc in raw_docs]
                        bm25 = BM25Okapi(tokenized_corpus)
                        tokenized_query = query.lower().split()
                        scores = bm25.get_scores(tokenized_query)
                        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
                        for idx in top_indices:
                            if scores[idx] > 0:
                                bm25_results.append(Document(
                                    page_content=raw_docs[idx]["page_content"],
                                    metadata=raw_docs[idx]["metadata"]
                                ))
                except Exception as e:
                    print(f"BM25 Search Error: {e}")

            # 3. Combine and Deduplicate
            combined_docs = []
            seen_contents = set()
            for doc in (vector_results + bm25_results):
                content_hash = hash(doc.page_content)
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    combined_docs.append(doc)
            
            if not combined_docs:
                return "No matching internal documentation found."
            
            return "\n\n".join([
                f"Source: {d.metadata.get('source', 'Unknown')}\nContent: {d.page_content}"
                for d in combined_docs
            ])

        self.tools = [
            get_system_status, 
            generate_secure_password, 
            test_network_latency,
            remember_fact, 
            self.web_search_tool,
            search_internal_knowledge
        ]

        # Create React agent using LangGraph prebuilt factory
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt="You are Telvyn, a helpful technical advisor AI. You have access to internal search, web search, system status, and password tools."
        )

    def stream_response(self, user_input, chat_history=[], session_id="default_session"):
        # Construct message objects list
        messages = []
        for msg in chat_history[-10:]:
            if msg["role"] == "human":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=user_input))
        
        try:
            seen_ids = set()
            for event in self.agent.stream({"messages": messages}, stream_mode="updates"):
                for node, update in event.items():
                    if "messages" in update:
                        for msg in update["messages"]:
                            msg_id = getattr(msg, "id", None)
                            if msg_id in seen_ids:
                                continue
                            if msg_id:
                                seen_ids.add(msg_id)
                            
                            if isinstance(msg, AIMessage):
                                if msg.tool_calls:
                                    tool_name = msg.tool_calls[0]['name']
                                    yield f"THOUGHT: Telvyn is executing tool '{tool_name}'...\n"
                                elif msg.content:
                                    yield msg.content
        except Exception as e:
            yield f"Telvyn Agent Error: {str(e)}"

    def get_response(self, user_input, chat_history=[]):
        messages = []
        for msg in chat_history[-10:]:
            if msg["role"] == "human":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=user_input))
        
        result = self.agent.invoke({"messages": messages})
        return result["messages"][-1].content
