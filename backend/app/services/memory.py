"""
IRIS AI — Memory Manager
Handles vector-based semantic memory using ChromaDB, plus conversation
retrieval from PostgreSQL for short-term context.
"""
from typing import Optional, List
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings


class MemoryManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    # ─── Add Memory ───────────────────────────────────────────────────────────
    def add_memory(
        self,
        user_id: int,
        text: str,
        metadata: Optional[dict] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        """Store a piece of memory. Returns the memory ID."""
        if metadata is None:
            metadata = {}

        doc_id = memory_id or f"u{user_id}_{hash(text) & 0xFFFFFFFF}"

        # Clamp user_id into metadata as string (ChromaDB needs strings)
        full_metadata = {"user_id": str(user_id), **metadata}

        self.collection.upsert(
            documents=[text],
            metadatas=[full_metadata],
            ids=[doc_id],
        )
        return doc_id

    # ─── Query Memory ─────────────────────────────────────────────────────────
    def query_memory(
        self,
        user_id: int,
        query: str,
        n_results: int = 5,
        memory_type: Optional[str] = None,
    ) -> List[str]:
        """
        Semantic search in user's memory.
        Returns list of relevant text documents.
        """
        where = {"user_id": str(user_id)}
        if memory_type:
            where["type"] = memory_type

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self._count_user_docs(user_id)),
                where=where,
            )
            docs = results.get("documents", [[]])[0]
            return docs
        except Exception:
            return []

    def _count_user_docs(self, user_id: int) -> int:
        """Count documents for a user (needed to avoid n_results > count error)."""
        try:
            result = self.collection.get(where={"user_id": str(user_id)})
            return max(1, len(result.get("ids", [])))
        except Exception:
            return 1

    # ─── Store User Preferences ───────────────────────────────────────────────
    def save_preference(self, user_id: int, key: str, value: str):
        """Store a named user preference (upsert by key)."""
        self.add_memory(
            user_id=user_id,
            text=f"User preference: {key} = {value}",
            metadata={"type": "preference", "key": key},
            memory_id=f"pref_{user_id}_{key}",
        )

    def get_preference(self, user_id: int, key: str) -> Optional[str]:
        """Retrieve a specific user preference."""
        try:
            result = self.collection.get(ids=[f"pref_{user_id}_{key}"])
            docs = result.get("documents", [])
            return docs[0] if docs else None
        except Exception:
            return None

    # ─── Delete Memory ────────────────────────────────────────────────────────
    def delete_memory(self, memory_id: str):
        """Delete a specific memory by ID."""
        try:
            self.collection.delete(ids=[memory_id])
        except Exception:
            pass

    def clear_user_memory(self, user_id: int):
        """Delete ALL memory for a user (use with caution)."""
        try:
            result = self.collection.get(where={"user_id": str(user_id)})
            ids = result.get("ids", [])
            if ids:
                self.collection.delete(ids=ids)
        except Exception:
            pass

    # ─── Context Builder ──────────────────────────────────────────────────────
    def build_context_string(self, user_id: int, query: str) -> str:
        """Build a memory context string to inject into LLM prompts."""
        memories = self.query_memory(user_id, query, n_results=3)
        if not memories:
            return ""
        return "\n".join(f"- {m}" for m in memories)


memory_manager = MemoryManager()
