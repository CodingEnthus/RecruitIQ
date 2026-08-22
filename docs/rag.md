# RAG Architecture & Recruiter Co-Pilot

RecruitIQ features a grounded Retrieval-Augmented Generation (RAG) assistant allowing recruiters to query candidate knowledge bases interactively.

## Pipeline Architecture

1. **Query Processing**: Normalizes recruiter query and extracts domain filters.
2. **Hybrid Retrieval**: Queries Qdrant dense vectors (BGE-M3) and BM25 sparse index concurrently.
3. **RRF Ranking**: Blends dense and sparse candidate evidence chunks using Reciprocal Rank Fusion.
4. **Cross-Encoder Reranking**: Reranks top 15 candidate chunks using BAAI/bge-reranker-v2-m3.
5. **Grounded Synthesis**: Prompts Groq LLM (LLaMA 3.3 70B) to synthesize answers referencing ONLY retrieved context.
6. **Evidence Citations**: Attaches explicit candidate name, section, and text excerpt citations to every response.
