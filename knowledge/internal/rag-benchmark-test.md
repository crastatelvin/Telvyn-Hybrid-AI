# Enterprise RAG Benchmark Dataset

## Document ID
DOC-001

### BM25 Retrieval Test Queries

Query 1:
How does hybrid search combine dense vectors and BM25 ranking?

Expected Match:
Section: Hybrid Retrieval Architecture

Query 2:
What causes embedding drift in production RAG systems?

Expected Match:
Section: Embedding Drift

Query 3:
How can chunk overlap improve retrieval accuracy?

Expected Match:
Section: Chunking Strategies

---

# Hybrid Retrieval Architecture

Modern Retrieval-Augmented Generation (RAG) systems frequently use hybrid search.

Hybrid search combines:
- BM25 lexical retrieval
- Dense vector similarity search
- Reciprocal Rank Fusion (RRF)

Benefits:
- Better keyword matching
- Improved semantic retrieval
- Reduced false negatives

Keywords:
BM25, lexical search, hybrid retrieval, dense embeddings, vector database, RRF

---

# Embedding Drift

Embedding drift occurs when:
- New embedding models are deployed
- Data distributions change
- Domain vocabulary evolves

Common Symptoms:
- Lower retrieval precision
- Reduced recall
- Ranking instability

Mitigation:
- Re-embedding pipelines
- A/B evaluation
- Benchmark testing

Keywords:
embedding drift, vector degradation, retrieval precision, semantic search

---

# Chunking Strategies

Chunk size significantly impacts retrieval quality.

Common approaches:
1. Fixed-size chunking
2. Recursive chunking
3. Semantic chunking

Best Practices:
- 200–500 token chunks
- 10–20% overlap
- Preserve section boundaries

Keywords:
chunk overlap, semantic chunking, recursive splitter, tokenization

---

# Vector Databases

Popular vector databases include:
- Pinecone
- Weaviate
- Qdrant
- Milvus

Evaluation Metrics:
- Recall@K
- Precision@K
- MRR
- NDCG

Keywords:
vector database, ANN search, HNSW, similarity search

---

# Agentic RAG

Agentic RAG extends traditional retrieval by allowing agents to:
- Plan retrieval steps
- Query multiple tools
- Verify evidence
- Self-correct responses

Keywords:
agent workflow, tool calling, reasoning loop, evidence validation

---

# Benchmark Questions

1. What is Reciprocal Rank Fusion?
2. Name two causes of embedding drift.
3. Which metrics evaluate retrieval quality?
4. What are the advantages of hybrid search?
5. What role does chunk overlap play in RAG?

