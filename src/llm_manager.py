import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

TELVYN_SYSTEM_PROMPT = """
You are "Telvyn", a senior technical advisor. 
Your goal is to provide concise, scannable, and actionable advice.

RULES:
1. BREVITY: Keep answers under 3 paragraphs unless requested otherwise.
2. SCANNABILITY: Use bullet points or bold text for key takeaways.
3. NEXT STEPS: Always end with a single, clear "Next Step".
4. PRIVACY: If the user asks about sensitive data not in your context, refuse politely.
5. SOURCE: Use the provided context to answer internal questions. If context is missing, state it.

Context:
{context}
"""

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class TelvynManager:
    def __init__(self, db_dir="./data/chroma_db"):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
            
        self.llm = ChatGroq(
            temperature=0.2,
            model_name="llama-3.3-70b-versatile",
            groq_api_key=self.api_key
        )
        
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db_dir = db_dir
        
        # Initialize vector store
        if os.path.exists(self.db_dir):
            self.vector_db = Chroma(
                persist_directory=self.db_dir, 
                embedding_function=self.embeddings
            )
        else:
            self.vector_db = None

    def get_response(self, user_query):
        if not self.vector_db:
            return "Knowledge base not initialized. Please run ingestion first."

        retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", TELVYN_SYSTEM_PROMPT),
            ("human", "{input}")
        ])
        
        # LCEL Chain
        rag_chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        response = rag_chain.invoke(user_query)
        return response
