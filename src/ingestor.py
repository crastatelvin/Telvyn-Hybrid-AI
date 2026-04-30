import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

class TelvynIngestor:
    def __init__(self, knowledge_dir="./knowledge", db_dir="./data/chroma_db"):
        self.knowledge_dir = knowledge_dir
        self.db_dir = db_dir
        # Using a lightweight local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
    def sync_knowledge(self):
        """Processes .md files and updates the ChromaDB index."""
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)
            print(f"Created {self.knowledge_dir}. Add .md files there.")
            return

        print(f"Loading documents from {self.knowledge_dir}...")
        loader = DirectoryLoader(
            self.knowledge_dir, 
            glob="**/*.md", 
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        
        documents = loader.load()
        if not documents:
            print("No .md files found in the knowledge directory.")
            return

        print(f"Splitting {len(documents)} documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(documents)

        print(f"Indexing {len(chunks)} chunks into ChromaDB at {self.db_dir}...")
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_dir
        )
        # Chroma handles persistence automatically in newer versions, 
        # but calling persist() is a good habit for compatibility if needed.
        # vector_db.persist() 
        print("Knowledge synchronization complete.")

if __name__ == "__main__":
    ingestor = TelvynIngestor()
    ingestor.sync_knowledge()
