"""
IRIS AI — Memory Search Endpoints
Allows querying and managing the long-term vector memory store.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.models.user import User
from app.services.memory import memory_manager
from app.api.deps import get_current_user

router = APIRouter()


class MemoryAddRequest(BaseModel):
    text: str
    memory_type: str = "manual"


class MemorySearchResult(BaseModel):
    documents: List[str]
    query: str


@router.get("/search", response_model=MemorySearchResult)
def search_memory(
    q: str = Query(..., description="Semantic search query"),
    n: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    """Semantically search the user's long-term memory."""
    docs = memory_manager.query_memory(current_user.id, q, n_results=n)
    return MemorySearchResult(documents=docs, query=q)


@router.post("/", status_code=201)
def add_memory(
    body: MemoryAddRequest,
    current_user: User = Depends(get_current_user),
):
    """Manually add a memory entry."""
    mem_id = memory_manager.add_memory(
        user_id=current_user.id,
        text=body.text,
        metadata={"type": body.memory_type, "source": "manual"},
    )
    return {"id": mem_id, "text": body.text}


@router.delete("/{memory_id}")
def delete_memory_entry(
    memory_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a specific memory entry by ID."""
    memory_manager.delete_memory(memory_id)
    return {"deleted": memory_id}


@router.delete("/")
def clear_all_memory(current_user: User = Depends(get_current_user)):
    """Clear all memory for the current user."""
    memory_manager.clear_user_memory(current_user.id)
    return {"message": "All memory cleared."}
