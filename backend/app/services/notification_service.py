"""
IRIS AI — Notification Service
Handles push notifications to devices and in-app alerts using Redis pub/sub.
"""
import json
import redis.asyncio as aioredis
from typing import Optional
from app.core.config import settings
from app.websockets.manager import manager


class NotificationService:
    def __init__(self):
        self.redis_url = settings.REDIS_URL

    async def push_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "info",
        data: Optional[dict] = None,
    ):
        """
        Push a notification to all connected devices of a user.
        notification_type: 'info' | 'warning' | 'error' | 'reminder'
        """
        payload = json.dumps({
            "type": "notification",
            "notification": {
                "title": title,
                "body": body,
                "notification_type": notification_type,
                "data": data or {},
            },
        })
        await manager.broadcast_to_user(user_id, payload)

    async def push_to_device(
        self,
        user_id: int,
        device_id: str,
        title: str,
        body: str,
        notification_type: str = "info",
    ):
        """Push a notification to a specific device."""
        payload = {
            "type": "notification",
            "notification": {
                "title": title,
                "body": body,
                "notification_type": notification_type,
            },
        }
        await manager.send_command_to_device(user_id, device_id, payload)

    async def broadcast_system_event(self, user_id: int, event: str, data: dict):
        """Broadcast a system event (e.g. device-connected, reminder-fired)."""
        payload = json.dumps({
            "type": "system_event",
            "event": event,
            "data": data,
        })
        await manager.broadcast_to_user(user_id, payload)


notification_service = NotificationService()
