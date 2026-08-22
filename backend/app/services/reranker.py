from typing import List, Dict, Any
from rapidfuzz import fuzz

class RerankerEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RerankerEngine, cls).__new__(cls)
            cls._instance._cross_encoder = None
            try:
                from sentence_transformers import CrossEncoder
                cls._instance._cross_encoder = CrossEncoder('BAAI/bge-reranker-v2-m3')
            except Exception as e:
                print(f"[RerankerEngine] BGE-Reranker v2 M3 load fallback to cross-score heuristic: {e}")
                cls._instance._cross_encoder = None
        return cls._instance

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        if self._cross_encoder is not None:
            try:
                pairs = [[query, c.get("text", "")] for c in chunks]
                scores = self._cross_encoder.predict(pairs)
                for c, s in zip(chunks, scores):
                    c["reranker_score"] = float(s)
                sorted_chunks = sorted(chunks, key=lambda x: x["reranker_score"], reverse=True)
                return sorted_chunks[:top_n]
            except Exception as e:
                print(f"[RerankerEngine] Reranker prediction fallback: {e}")

        # Heuristic cross-encoder scoring fallback
        for c in chunks:
            text = c.get("text", "")
            # Token match + fuzzy similarity score
            q_terms = query.lower().split()
            matches = sum(1 for t in q_terms if t in text.lower())
            fuzz_score = fuzz.partial_ratio(query.lower(), text.lower()) / 100.0
            c["reranker_score"] = (matches * 0.5) + (fuzz_score * 0.5)

        sorted_chunks = sorted(chunks, key=lambda x: x["reranker_score"], reverse=True)
        return sorted_chunks[:top_n]
