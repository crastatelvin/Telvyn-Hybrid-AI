import os
import json
import hashlib
import time
import re
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

class TelvynIngestor:
    def __init__(self, knowledge_dir=None, db_dir=None):
        self.knowledge_dir = knowledge_dir or os.getenv("KNOWLEDGE_DIR", "./knowledge")
        self.db_dir = db_dir or os.getenv("DB_DIR", "./data/chroma_db")
        
        # Lightweight local embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
    def get_file_hash(self, filepath):
        """Returns MD5 hash of a file."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def sync_knowledge(self):
        """Processes .md files and updates the ChromaDB + BM25 index if changes are detected."""
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)
            return

        hash_file = os.path.join(self.db_dir, "file_hashes.json")
        os.makedirs(self.db_dir, exist_ok=True)
        
        current_hashes = {}
        if os.path.exists(hash_file):
            try:
                with open(hash_file, "r") as f:
                    current_hashes = json.load(f)
            except Exception as e:
                print(f"Error loading file hashes: {e}")

        # Scan for md files and calculate hashes
        detected_files = {}
        for root, _, files in os.walk(self.knowledge_dir):
            for file in files:
                if file.endswith(".md"):
                    filepath = os.path.join(root, file)
                    try:
                        detected_files[filepath] = self.get_file_hash(filepath)
                    except Exception as e:
                        print(f"Error reading file {filepath}: {e}")

        # Check if there is any mismatch (added, modified, or removed files)
        has_changes = False
        if len(detected_files) != len(current_hashes):
            has_changes = True
        else:
            for path, file_hash in detected_files.items():
                if path not in current_hashes or current_hashes[path] != file_hash:
                    has_changes = True
                    break

        if not has_changes:
            print("No changes detected in knowledge base.")
            return

        print("Changes detected. Re-indexing knowledge base...")
        
        # Load and parse all documents
        all_docs = []
        for filepath in detected_files.keys():
            try:
                loader = TextLoader(filepath, encoding='utf-8')
                loaded_docs = loader.load()
                for doc in loaded_docs:
                    # Find a title
                    title_match = re.search(r'^#\s+(.*)', doc.page_content, re.MULTILINE)
                    doc.metadata["title"] = title_match.group(1).strip() if title_match else os.path.basename(filepath)
                    doc.metadata["source"] = filepath
                    doc.metadata["last_updated"] = time.strftime('%Y-%m-%d %H:%M:%S')
                all_docs.extend(loaded_docs)
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

        if not all_docs:
            print("No documents to index.")
            # Clear indexes if empty
            if os.path.exists(self.db_dir):
                import shutil
                shutil.rmtree(self.db_dir)
                os.makedirs(self.db_dir, exist_ok=True)
            with open(hash_file, "w") as f:
                json.dump({}, f)
            return

        # Split docs into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(all_docs)
        print(f"Generated {len(chunks)} chunks from {len(all_docs)} documents.")

        # Re-build ChromaDB index
        # To avoid duplicated / stale chunks from modified/deleted files, we rebuild the DB
        # Chroma handles directory recreation automatically when we initialize with client
        try:
            # Delete old DB directory to ensure complete clean slate
            import shutil
            for item in os.listdir(self.db_dir):
                item_path = os.path.join(self.db_dir, item)
                if item != "file_hashes.json":
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
        except Exception as e:
            print(f"Warning clearing directory: {e}")

        print("Writing to ChromaDB...")
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_dir
        )
        vector_db.persist()

        # Update BM25 documents
        bm25_docs_path = os.path.join(self.db_dir, "bm25_docs.json")
        bm25_docs = []
        for chunk in chunks:
            bm25_docs.append({
                "page_content": chunk.page_content,
                "metadata": chunk.metadata
            })
            
        with open(bm25_docs_path, "w", encoding="utf-8") as f:
            json.dump(bm25_docs, f, ensure_ascii=False, indent=2)

        # Update hash file
        with open(hash_file, "w") as f:
            json.dump(detected_files, f)
            
        print("Knowledge synchronization complete.")

if __name__ == "__main__":
    ingestor = TelvynIngestor()
    ingestor.sync_knowledge()
