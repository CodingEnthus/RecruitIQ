import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.core.config import settings

class VectorStoreService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        if settings.QDRANT_URL and settings.QDRANT_API_KEY:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            # Shared local in-memory storage mode for process-level safety
            self.client = QdrantClient(":memory:")

        self.collection_name = settings.QDRANT_COLLECTION
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)  # BGE-M3 1024 dimensions
                )
        except Exception as e:
            print(f"[VectorStore] Collection check error: {e}")

    def upsert_chunks(self, candidate_id: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{candidate_id}_{chunk.get('section', 'sec')}_{idx}"))
            payload = {
                "candidate_id": candidate_id,
                "candidate_name": chunk.get("candidate_name", ""),
                "section": chunk.get("section", "summary"),
                "text": chunk.get("text", ""),
                "technologies": chunk.get("technologies", []),
                "role": chunk.get("role", ""),
                "company": chunk.get("company", "")
            }
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def search_similar(self, query_vector: List[float], candidate_ids: Optional[List[str]] = None, top_k: int = 15) -> List[Dict[str, Any]]:
        query_filter = None
        if candidate_ids:
            # Filter by candidate IDs
            query_filter = Filter(
                should=[FieldCondition(key="candidate_id", match=MatchValue(value=cid)) for cid in candidate_ids]
            )

        try:
            results = []
            if hasattr(self.client, "query_points"):
                res_obj = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )
                results = getattr(res_obj, "points", res_obj)
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )

            hits = []
            for res in results:
                hits.append({
                    "id": res.id,
                    "score": getattr(res, "score", 0.0),
                    "payload": res.payload
                })
            return hits
        except Exception as e:
            print(f"[VectorStore] Search error: {e}")
            return []


    def delete_candidate_vectors(self, candidate_id: str):
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="candidate_id", match=MatchValue(value=candidate_id))]
                )
            )
        except Exception as e:
            print(f"[VectorStore] Delete candidate error: {e}")

    def delete_all_vectors(self):
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection()
        except Exception as e:
            print(f"[VectorStore] Delete all error: {e}")

