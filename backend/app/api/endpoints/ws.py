"""
IRIS AI — WebSocket Endpoints
Real-time bidirectional communication hub for all devices.

Message types received from client:
  - voice_command: {type, content, conversation_id?}
  - telemetry:     {type, data: {cpu, ram, battery, disk, network}}
  - notification:  {type, title, body, notification_type}
  - command_result:{type, command_id, success, output}
  - pong:          {type}
  
Message types sent to client:
  - llm_chunk:     {type, content}         (streaming delta)
  - llm_response:  {type, content, intent, command}
  - command:       {type, data: {action, ...params}}
  - notification:  {type, notification: {title, body, notification_type}}
  - system_event:  {type, event, data}
  - ping:          {type}
  - connected:     {type, device_id, user_id}
"""
import json
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.device import Device
from app.websockets.manager import manager
from app.services.llm import llm_service
from app.services.memory import memory_manager
from app.services.automation_service import automation_service
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter()


async def _authenticate_ws(token: str) -> tuple[int | None, str | None]:
    """Validate JWT token from WebSocket query param. Returns (user_id, error)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None, "Missing subject in token"
        return int(user_id), None
    except JWTError as e:
        return None, str(e)


def _update_device_status(device_name: str, user_id: int, status: str, telemetry: dict = None):
    """Update device status/telemetry in the database."""
    db: Session = SessionLocal()
    try:
        device = db.query(Device).filter(
            Device.user_id == user_id,
            Device.device_name == device_name,
        ).first()
        if device:
            device.status = status
            device.last_seen = datetime.now(timezone.utc)
            if telemetry:
                device.telemetry = telemetry
            db.commit()
    except Exception:
        pass
    finally:
        db.close()


@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str, token: str = ""):
    """
    Main WebSocket endpoint for all IRIS clients.
    
    Connection URL: ws://server/api/v1/ws/{device_id}?token=<jwt>
    
    device_id: A unique identifier for this device/connection (e.g. 'desktop-main', 'android-pixel6')
    """
    # ── Authentication ────────────────────────────────────────────────────────
    user_id, error = await _authenticate_ws(token)
    if not user_id:
        await websocket.accept()
        await websocket.send_text(json.dumps({"type": "error", "message": f"Auth failed: {error}"}))
        await websocket.close(code=1008)
        return

    # ── Connect ───────────────────────────────────────────────────────────────
    await manager.connect(websocket, user_id, device_id)
    _update_device_status(device_id, user_id, "online")

    await websocket.send_text(json.dumps({
        "type": "connected",
        "device_id": device_id,
        "user_id": user_id,
        "message": "Connected to IRIS Central Server",
    }))

    # ── Announce to other devices ─────────────────────────────────────────────
    await manager.broadcast_to_user(user_id, json.dumps({
        "type": "system_event",
        "event": "device_connected",
        "data": {"device_id": device_id},
    }))

    # ── Heartbeat task ────────────────────────────────────────────────────────
    async def heartbeat():
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_text(json.dumps({"type": "ping"}))
            except Exception:
                break

    asyncio.create_task(heartbeat())

    # ── Message loop ──────────────────────────────────────────────────────────
    db: Session = SessionLocal()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            # ── Voice/Text Command → LLM ──────────────────────────────────────
            if msg_type in ("voice_command", "chat_message"):
                content = msg.get("content", "").strip()
                conv_id = msg.get("conversation_id")
                if not content:
                    continue

                # Get or create conversation
                if conv_id:
                    conversation = db.query(Conversation).filter(
                        Conversation.id == conv_id,
                        Conversation.user_id == user_id,
                    ).first()
                else:
                    conversation = Conversation(
                        user_id=user_id,
                        title=content[:60],
                    )
                    db.add(conversation)
                    db.flush()

                # Save user message
                user_msg_record = Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=content,
                )
                db.add(user_msg_record)
                db.flush()

                # Get conversation history
                history = [
                    {"role": m.role, "content": m.content}
                    for m in conversation.messages[:-1]  # exclude the one we just added
                ]

                # Get memory context
                memory_ctx = memory_manager.build_context_string(user_id, content)

                # Get user info
                user_obj = db.query(User).filter(User.id == user_id).first()
                user_info = f"Name: {user_obj.full_name or user_obj.email}" if user_obj else ""

                # Send typing indicator
                await websocket.send_text(json.dumps({"type": "typing_start"}))

                # Stream LLM response
                full_response = ""
                intent = None
                command = None
                model_used = None

                async for chunk_json in llm_service.generate_response_stream(
                    user_message=content,
                    conversation_history=history,
                    memory_context=memory_ctx,
                    user_info=user_info,
                ):
                    chunk = json.loads(chunk_json)
                    if chunk["type"] == "delta":
                        full_response += chunk.get("content", "")
                        await websocket.send_text(json.dumps({
                            "type": "llm_chunk",
                            "content": chunk.get("content", ""),
                            "conversation_id": conversation.id,
                        }))
                    elif chunk["type"] == "done":
                        intent = chunk.get("intent")
                        command = chunk.get("command")
                        model_used = chunk.get("model")

                # Send end of stream signal
                await websocket.send_text(json.dumps({
                    "type": "llm_response",
                    "content": full_response,
                    "conversation_id": conversation.id,
                    "intent": intent,
                    "command": command,
                }))

                # Save assistant message to DB
                ai_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    model_used=model_used,
                )
                db.add(ai_msg)
                db.commit()

                # Store in vector memory
                memory_manager.add_memory(
                    user_id=user_id,
                    text=f"User: {content}\nIRIS: {full_response}",
                    metadata={"type": "conversation", "conversation_id": str(conversation.id)},
                )

                # Dispatch device command if action was detected
                if intent and command:
                    await automation_service.dispatch_command(
                        user_id=user_id,
                        intent=intent,
                        command=command,
                        target_device_id=None,  # broadcast to all devices
                    )

            # ── Telemetry Update ──────────────────────────────────────────────
            elif msg_type == "telemetry":
                telemetry_data = msg.get("data", {})
                _update_device_status(device_id, user_id, "online", telemetry_data)

                # Broadcast telemetry to web dashboard
                await manager.broadcast_to_user(user_id, json.dumps({
                    "type": "device_telemetry",
                    "device_id": device_id,
                    "data": telemetry_data,
                }))

            # ── Notification Forwarding ───────────────────────────────────────
            elif msg_type == "notification":
                # Forward notification from mobile to all other devices
                await manager.broadcast_to_user(user_id, json.dumps({
                    "type": "notification",
                    "source_device": device_id,
                    "notification": msg.get("notification", {}),
                }))

            # ── Command Result ────────────────────────────────────────────────
            elif msg_type == "command_result":
                await manager.broadcast_to_user(user_id, json.dumps({
                    "type": "command_result",
                    "device_id": device_id,
                    "result": msg,
                }))

            # ── Pong (heartbeat response) ─────────────────────────────────────
            elif msg_type == "pong":
                pass  # Just keeping the connection alive

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
    finally:
        manager.disconnect(user_id, device_id)
        _update_device_status(device_id, user_id, "offline")
        db.close()

        # Announce disconnect to other devices
        try:
            await manager.broadcast_to_user(user_id, json.dumps({
                "type": "system_event",
                "event": "device_disconnected",
                "data": {"device_id": device_id},
            }))
        except Exception:
            pass
