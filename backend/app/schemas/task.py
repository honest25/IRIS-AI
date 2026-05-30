from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Note Schemas ─────────────────────────────────────────────────────────────
class NoteBase(BaseModel):
    title: str
    content: Optional[str] = None
    tags: Optional[str] = None


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_pinned: Optional[bool] = None


class NoteResponse(NoteBase):
    id: int
    user_id: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Reminder Schemas ─────────────────────────────────────────────────────────
class ReminderCreate(BaseModel):
    message: str
    trigger_at: datetime
    repeat_interval: Optional[str] = None   # daily | weekly | monthly


class ReminderResponse(ReminderCreate):
    id: int
    user_id: int
    is_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True
