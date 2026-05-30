"""
IRIS AI — WebSocket Connection Manager
Manages all real-time device connections with heartbeat and offline queuing.
"""
import json
import asyncio
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Maps user_id -> {device_id: WebSocket}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        # Offline message queue: user_id -> {device_id: [messages]}
        self.offline_queue: Dict[int, Dict[str, List[str]]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, device_id: str):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][device_id] = websocket

        # Drain queued messages for this device
        if user_id in self.offline_queue:
            queued = self.offline_queue[user_id].pop(device_id, [])
            for msg in queued:
                await websocket.send_text(msg)

    def disconnect(self, user_id: int, device_id: str):
        """Remove a disconnected device."""
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(device_id, None)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    def is_connected(self, user_id: int, device_id: str) -> bool:
        return (
            user_id in self.active_connections
            and device_id in self.active_connections[user_id]
        )

    def get_connected_devices(self, user_id: int) -> List[str]:
        return list(self.active_connections.get(user_id, {}).keys())

    async def send_to_device(self, user_id: int, device_id: str, message: str):
        """Send a message to a specific device. Queues if offline."""
        if self.is_connected(user_id, device_id):
            try:
                ws = self.active_connections[user_id][device_id]
                await ws.send_text(message)
            except Exception:
                self.disconnect(user_id, device_id)
                self._queue_message(user_id, device_id, message)
        else:
            self._queue_message(user_id, device_id, message)

    async def send_command_to_device(
        self, user_id: int, device_id: str, command: dict
    ) -> bool:
        """Send a JSON command to a device. Returns True if delivered live."""
        payload = json.dumps(command)
        if self.is_connected(user_id, device_id):
            try:
                ws = self.active_connections[user_id][device_id]
                await ws.send_text(payload)
                return True
            except Exception:
                self.disconnect(user_id, device_id)
        self._queue_message(user_id, device_id, payload)
        return False

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a raw text message to a specific WebSocket."""
        await websocket.send_text(message)

    async def broadcast_to_user(self, user_id: int, message: str):
        """Broadcast a message to ALL devices of a user."""
        if user_id not in self.active_connections:
            return
        dead = []
        for device_id, ws in self.active_connections[user_id].items():
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(device_id)
        for device_id in dead:
            self.disconnect(user_id, device_id)

    async def ping_device(self, user_id: int, device_id: str) -> bool:
        """Send a ping and check if device is still alive."""
        if not self.is_connected(user_id, device_id):
            return False
        try:
            ws = self.active_connections[user_id][device_id]
            await ws.send_text(json.dumps({"type": "ping"}))
            return True
        except Exception:
            self.disconnect(user_id, device_id)
            return False

    def _queue_message(self, user_id: int, device_id: str, message: str):
        """Add a message to the offline queue for a device."""
        if user_id not in self.offline_queue:
            self.offline_queue[user_id] = {}
        if device_id not in self.offline_queue[user_id]:
            self.offline_queue[user_id][device_id] = []
        # Limit queue size to 50 messages
        queue = self.offline_queue[user_id][device_id]
        if len(queue) < 50:
            queue.append(message)


manager = ConnectionManager()
