"""
IRIS AI — Automation Service
Routes [ACTION:...] commands from LLM responses to the correct device
via the WebSocket connection manager.
"""
import json
from typing import Optional
from app.websockets.manager import manager


class AutomationService:
    """
    Parses LLM intent and dispatches commands to connected devices.
    Supports targeting a specific device or broadcasting to all user devices.
    """

    async def dispatch_command(
        self,
        user_id: int,
        intent: str,
        command: dict,
        target_device_id: Optional[str] = None,
    ) -> dict:
        """
        Send a command to a device.

        Args:
            user_id: The authenticated user's ID
            intent: Action name (e.g. 'lock_screen')
            command: Full command dict with action + params
            target_device_id: Specific device, or None to broadcast

        Returns:
            dict with success status
        """
        payload = {
            "type": "command",
            "data": {
                "action": intent,
                **command.get("params", {}),
            },
        }

        if target_device_id:
            success = await manager.send_command_to_device(
                user_id, target_device_id, payload
            )
            return {"dispatched": success, "device_id": target_device_id}
        else:
            # Broadcast to all connected devices (desktop agent picks it up)
            await manager.broadcast_to_user(user_id, json.dumps(payload))
            return {"dispatched": True, "device_id": "all"}

    def build_command_payload(self, action: str, params: dict) -> dict:
        """Build a standardized command payload."""
        return {
            "type": "command",
            "data": {"action": action, **params},
        }

    def get_supported_actions(self) -> list:
        """Return list of supported device actions."""
        return [
            "lock_screen", "sleep", "shutdown", "restart",
            "open_app", "close_app",
            "open_browser",
            "set_volume", "set_brightness",
            "take_screenshot",
            "search_files",
            "type_text", "mouse_move", "mouse_click",
            "send_whatsapp", "send_sms", "make_call",
        ]


automation_service = AutomationService()
