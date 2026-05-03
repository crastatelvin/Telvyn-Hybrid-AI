import os
import json
import hashlib
import time
import re
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

class TelvynIngestor:
    def __init__(self, knowledge_dir="./knowledge", db_dir="./data/chroma_db"):
        self.knowledge_dir = knowledge_dir
        self.db_dir = db_dir
        # Using a lightweight local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
    def get_file_hash(self, filepath):
        """Returns the MD5 hash of a file."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def sync_knowledge(self):
        """Processes .md files and updates the ChromaDB index incrementally."""
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)
            return

        hash_file = os.path.join(self.db_dir, "file_hashes.json")
        os.makedirs(self.db_dir, exist_ok=True)
        
        current_hashes = {}
        if os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                current_hashes = json.load(f)

        new_hashes = {}
        docs_to_process = []
        
        # Walk through directory to find .md files
        for root, _, files in os.walk(self.knowledge_dir):
            for file in files:
                if file.endswith(".md"):
                    filepath = os.path.join(root, file)
                    file_hash = self.get_file_hash(filepath)
                    new_hashes[filepath] = file_hash
                    
                    if filepath not in current_hashes or current_hashes[filepath] != file_hash:
                        print(f"Detected change in: {file}")
                        loader = TextLoader(filepath, encoding='utf-8')
                        loaded_docs = loader.load()
                        
                        # Simple Metadata Extraction
                        for doc in loaded_docs:
                            # Try to find a title in the first few lines
                            title_match = re.search(r'^#\s+(.*)', doc.page_content, re.MULTILINE)
                            if title_match:
                                doc.metadata["title"] = title_match.group(1).strip()
                            
                            doc.metadata["source"] = filepath
                            doc.metadata["last_updated"] = time.strftime('%Y-%m-%d %H:%M:%S')
                            
                        docs_to_process.extend(loaded_docs)

        if not docs_to_process:
            print("No new or modified documents found.")
            return

        print(f"Splitting {len(docs_to_process)} documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(docs_to_process)

        print(f"Updating FAISS index at {self.db_dir}...")
        faiss_index_path = os.path.join(self.db_dir, "faiss_index")
        
        # Initialize or load existing DB
        if os.path.exists(faiss_index_path):
            vector_db = FAISS.load_local(
                faiss_index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True # Required for loading local FAISS
            )
            vector_db.add_documents(chunks)
        else:
            vector_db = FAISS.from_documents(chunks, self.embeddings)
        
        # Save FAISS index
        vector_db.save_local(faiss_index_path)
        
        # Update hash file
        with open(hash_file, "w") as f:
            json.dump(new_hashes, f)
            
        print("Knowledge synchronization complete.")

if __name__ == "__main__":
    ingestor = TelvynIngestor()
    ingestor.sync_knowledge()
