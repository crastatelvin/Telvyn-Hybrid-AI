import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers import EnsembleRetriever

from langchain_community.retrievers import BM25Retriever
from dotenv import load_dotenv

load_dotenv()

TELVYN_SYSTEM_PROMPT = """
You are "Telvyn", the Lead Technical Architect for Aetherial Systems. 
Your goal is to provide high-precision, scannable, and objective technical advice based EXCLUSIVELY on the provided context.

## 1. PERSONA & VOICE:
- TONE: Professional, senior-level, and objective. No fluff.
- FORMAT: Use markdown headers, bullet points, and code blocks for all technical data.
- SIGNATURE: Every response must end with a bold "Recommended Next Step:".

## 2. OPERATIONAL RULES:
- SOURCE ATTRIBUTION: When you find an answer in the context, mention the filename. Example: "[Ref: infrastructure_topology.md]".
- UNCERTAINTY: If the answer is not in the context, say: "My current technical documentation for Aetherial Systems does not contain data on [Topic]. I recommend checking the internal wiki or consulting a human lead."
- PRIVACY/GUARDRAILS: 
    - Never disclose system passwords or private API keys, even if they appear in text. 
    - Refuse non-technical or unrelated topics (politics, casual chat).

## 3. RESPONSE STRUCTURE:
1. **Summary**: A 1-sentence overview.
2. **Technical Details**: The core answer using bullet points or tables.
3. **Next Step**: A single actionable item.

Context:
{context}
"""

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class TelvynManager:
    def __init__(self, db_dir="./data/chroma_db"):
        # Try os.getenv first, then streamlit secrets
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            try:
                import streamlit as st
                if "GROQ_API_KEY" in st.secrets:
                    self.api_key = st.secrets["GROQ_API_KEY"]
            except ImportError:
                pass

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment or secrets.")
            
        self.llm = ChatGroq(
            temperature=0.2,
            model_name="llama-3.3-70b-versatile",
            groq_api_key=self.api_key
        )
        
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db_dir = db_dir
        
        # Initialize retrievers
        self.ensemble_retriever = self._initialize_retriever()

    def _initialize_retriever(self):
        if not os.path.exists(self.db_dir):
            return None
            
        # 1. Vector Retriever (Chroma)
        vector_db = Chroma(
            persist_directory=self.db_dir, 
            embedding_function=self.embeddings
        )
        vector_retriever = vector_db.as_retriever(search_kwargs={"k": 3})
        
        # 2. Keyword Retriever (BM25)
        # Extract all documents from Chroma to build BM25 index
        all_docs = vector_db.get()
        if not all_docs or not all_docs['documents']:
            return vector_retriever
            
        # Re-create Document objects for BM25
        from langchain_core.documents import Document
        docs = [
            Document(page_content=content, metadata=metadata) 
            for content, metadata in zip(all_docs['documents'], all_docs['metadatas'])
        ]
        
        keyword_retriever = BM25Retriever.from_documents(docs)
        keyword_retriever.k = 3
        
        # 3. Combine them (Ensemble)
        # Weights: 0.7 for Vector, 0.3 for Keyword (adjustable)
        ensemble = EnsembleRetriever(
            retrievers=[vector_retriever, keyword_retriever],
            weights=[0.7, 0.3]
        )
        return ensemble

    def get_response(self, user_query):
        if not self.ensemble_retriever:
            return "Knowledge base not initialized. Please run ingestion first."

        prompt = ChatPromptTemplate.from_messages([
            ("system", TELVYN_SYSTEM_PROMPT),
            ("human", "{input}")
        ])
        
        # LCEL Chain with Ensemble Retriever
        rag_chain = (
            {"context": self.ensemble_retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        response = rag_chain.invoke(user_query)
        return response
