import math
import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.services.vector_store import VectorStoreService

class EmbeddingEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
            cls._instance._model = None
            try:
                from sentence_transformers import SentenceTransformer
                # Load BGE-M3 or fallback model gracefully
                cls._instance._model = SentenceTransformer('BAAI/bge-m3')
            except Exception as e:
                print(f"[EmbeddingEngine] Heavy BGE-M3 model load fallback to lightweight model or hashing vectorizer: {e}")
                try:
                    from sentence_transformers import SentenceTransformer
                    cls._instance._model = SentenceTransformer('all-MiniLM-L6-v2')
                except Exception:
                    cls._instance._model = None
        return cls._instance

    def encode(self, text: str) -> List[float]:
        if self._model is not None:
            emb = self._model.encode(text, convert_to_numpy=True).tolist()
            # If dimensions are smaller than 1024, pad to 1024 for Qdrant schema compatibility
            if len(emb) < 1024:
                emb = emb + [0.0] * (1024 - len(emb))
            elif len(emb) > 1024:
                emb = emb[:1024]
            return emb
        else:
            # Deterministic text feature hashing vectorizer (1024 dims) if torch/transformers unavailable
            vec = [0.0] * 1024
            words = re.findall(r'\w+', text.lower())
            for w in words:
                idx = abs(hash(w)) % 1024
                vec[idx] += 1.0
            norm = math.sqrt(sum(v*v for v in vec)) or 1.0
            return [v / norm for v in vec]

class HybridSearchService:
    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.embedding_engine = EmbeddingEngine()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.embedding_engine.encode(t) for t in texts]

    def hybrid_retrieve(self, query: str, all_candidate_chunks: List[Dict[str, Any]], top_k: int = 20) -> List[Dict[str, Any]]:
        if not all_candidate_chunks:
            return []

        # 1. Dense retrieval via Qdrant
        query_vector = self.embedding_engine.encode(query)
        dense_hits = self.vector_store.search_similar(query_vector, top_k=top_k * 2)

        dense_ranked_ids = []
        dense_chunk_map = {}
        for hit in dense_hits:
            chunk_id = hit["id"]
            dense_ranked_ids.append(chunk_id)
            dense_chunk_map[chunk_id] = hit["payload"]

        # 2. Sparse retrieval via BM25
        tokenized_corpus = [re.findall(r'\w+', c["text"].lower()) for c in all_candidate_chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = re.findall(r'\w+', query.lower())
        bm25_scores = bm25.get_scores(tokenized_query)

        # Pair chunks with scores & sort
        sparse_pairs = sorted(zip(all_candidate_chunks, bm25_scores), key=lambda x: x[1], reverse=True)
        sparse_ranked_chunks = [p[0] for p in sparse_pairs[:top_k * 2]]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        k_const = 60

        # Dense ranks
        for rank, hit in enumerate(dense_hits):
            cid = hit["id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_const + (rank + 1)))

        # Sparse ranks
        for rank, chunk in enumerate(sparse_ranked_chunks):
            cid = chunk.get("chunk_id", f"{chunk['candidate_id']}_{chunk['section']}")
            dense_chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_const + (rank + 1)))

        # Sort combined results by RRF score
        sorted_fusion = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        final_top_chunks = []
        for cid, score in sorted_fusion[:top_k]:
            chunk_data = dense_chunk_map.get(cid, {})
            if chunk_data:
                chunk_copy = dict(chunk_data)
                chunk_copy["rrf_score"] = score
                final_top_chunks.append(chunk_copy)

        return final_top_chunks
