# RecruitIQ System Architecture

RecruitIQ replaces black-box "LLM resume score generators" with a multi-stage, explainable hybrid AI retrieval and deterministic evaluation architecture.

```
                       ┌──────────────────────────────┐
                       │     Next.js 14 Dashboard     │
                       │ (TypeScript + Tailwind CSS)  │
                       └──────────────┬───────────────┘
                                      │ REST API
                                      ▼
                       ┌──────────────────────────────┐
                       │       FastAPI Backend        │
                       │    (Python 3.11 + Pydantic)  │
                       └──────────────┬───────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
  Resume Ingestor              Job Analyzer              PostgreSQL / SQLite
  (PyMuPDF + OCR)         (Groq API / Schema)            (SQLAlchemy ORM)
          │                           │
          ▼                           ▼
  Structured Extractor        Job Requirement Profile
          │                           │
          └──────────────┬────────────┘
                         ▼
                Skill Normalizer
           (Canonical Aliases + Fuzzy)
                         │
                         ▼
            Candidate Knowledge Base
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
    BGE-M3 Embeddings           BM25 Index
    (Qdrant Vector DB)       (Sparse Search)
             │                       │
             └───────────┬─────────┬─┘
                         ▼         │
               Hybrid RRF Search   │
                         │         │
                         ▼         │
             BGE-Reranker-v2-M3    │
                         │         │
                         ▼         ▼
             Top Relevant Evidence Chunks
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
   Deterministic Scoring     LLM Grounded Reasoning
   Engine (Config Weights)      (Groq API / RAG)
             │                       │
             └───────────┬───────────┘
                         ▼
                 Recruiter Output
         (Dashboard, Comparison, RAG Chat)
```

## Core Architectural Stages

1. **Ingestion & Sectioning**: Resumes in PDF/TXT format are validated, extracted via PyMuPDF, cleaned, and split into structured candidate sections (Summary, Skills, Experience, Education, Projects).
2. **Skill Normalization**: Aliases (e.g. `React.js` -> `React`, `Postgres` -> `PostgreSQL`, `ML` -> `Machine Learning`) are normalized using canonical dictionaries and fuzzy matching.
3. **Hybrid Search & Fusion**: Combines BGE-M3 dense vector embeddings (stored in Qdrant with payload metadata filtering) and BM25 sparse keyword indexing using Reciprocal Rank Fusion (RRF).
4. **Transformer Reranking**: Candidate chunks shortlisted via hybrid retrieval are reranked using BAAI/bge-reranker-v2-m3 cross-encoder scoring.
5. **Deterministic Scoring**: Calculates non-arbitrary scores based on 6 weighted components (Required Skills 35%, Semantic Fit 25%, Experience 15%, Education 10%, Projects 10%, Evidence Quality 5%).
6. **Grounded Reasoning & Recruiter RAG**: Synthesizes evidence-backed explanations and answers recruiter queries with explicit citations.
