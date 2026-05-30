# This module imports all models so that SQLAlchemy can discover them.
# Import order matters for foreign key resolution.
from app.models.user import User
from app.models.device import Device
from app.models.conversation import Conversation, Message
from app.models.task import Task, Note, Reminder
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "Device",
    "Conversation",
    "Message",
    "Task",
    "Note",
    "Reminder",
    "AuditLog",
]
