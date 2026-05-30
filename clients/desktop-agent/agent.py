"""
IRIS AI — Desktop Agent (Main)
Cross-platform agent that connects to the IRIS central server via WebSocket.
Handles: telemetry, voice commands, device control, and system tray.

Usage:
    python agent.py

Configuration:
    Copy .env.example to .env and fill in IRIS_AUTH_TOKEN.
"""
import asyncio
import json
import signal
import sys
import threading
import time
import os
from datetime import datetime

import websockets
from dotenv import load_dotenv

from commands import execute_command, get_telemetry
from voice import VoiceEngine
from tray import create_tray_icon

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
SERVER_WS_URL = os.getenv("IRIS_SERVER_WS_URL", "ws://localhost:8000/api/v1")
DEVICE_ID     = os.getenv("IRIS_DEVICE_ID", "desktop-main")
AUTH_TOKEN    = os.getenv("IRIS_AUTH_TOKEN", "")
TELEMETRY_INTERVAL = int(os.getenv("IRIS_TELEMETRY_INTERVAL", "10"))
ENABLE_VOICE  = os.getenv("IRIS_ENABLE_VOICE", "true").lower() == "true"
ENABLE_TRAY   = os.getenv("IRIS_ENABLE_TRAY", "true").lower() == "true"

# ─── Globals ──────────────────────────────────────────────────────────────────
_ws_connection = None   # Active websocket
_voice_engine: VoiceEngine | None = None
_running = True

# ─── Logging ──────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [IRIS] {msg}")


# ─── Voice → Server ───────────────────────────────────────────────────────────
async def send_voice_command(text: str):
    """Forward a voice command to the IRIS server."""
    if _ws_connection:
        try:
            await _ws_connection.send(json.dumps({
                "type": "voice_command",
                "content": text,
            }))
            log(f"Voice command sent: {text}")
        except Exception as e:
            log(f"Failed to send voice command: {e}")


def voice_command_callback(text: str):
    """Thread-safe callback from voice engine → asyncio."""
    if _ws_connection:
        asyncio.run_coroutine_threadsafe(
            send_voice_command(text),
            asyncio.get_event_loop(),
        )


# ─── Telemetry Loop ───────────────────────────────────────────────────────────
async def telemetry_loop(websocket):
    """Send system telemetry to the server every N seconds."""
    while _running:
        try:
            telemetry = get_telemetry()
            await websocket.send(json.dumps({
                "type": "telemetry",
                "data": telemetry,
            }))
        except Exception as e:
            log(f"Telemetry error: {e}")
            break
        await asyncio.sleep(TELEMETRY_INTERVAL)


# ─── Message Handler ──────────────────────────────────────────────────────────
async def handle_message(message: str):
    """Process a message from the IRIS server."""
    global _ws_connection
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return

    msg_type = data.get("type", "")

    if msg_type == "connected":
        log(f"✅ Connected to IRIS Server. Device: {data.get('device_id')}")

    elif msg_type == "command":
        # Execute the device command
        result = execute_command(data.get("data", {}))
        log(f"Command result: {result}")
        # Send result back
        if _ws_connection:
            await _ws_connection.send(json.dumps({
                "type": "command_result",
                "result": result,
            }))

    elif msg_type == "llm_response":
        content = data.get("content", "")
        log(f"IRIS: {content[:100]}{'...' if len(content) > 100 else ''}")
        # Speak the response
        if _voice_engine and content:
            _voice_engine.speak(content)

    elif msg_type == "llm_chunk":
        # Streaming chunk — just print to console
        chunk = data.get("content", "")
        if chunk:
            print(chunk, end="", flush=True)

    elif msg_type == "notification":
        notif = data.get("notification", {})
        log(f"🔔 {notif.get('title', '')}: {notif.get('body', '')}")
        # Show OS notification
        _show_os_notification(notif.get("title", "IRIS"), notif.get("body", ""))

    elif msg_type == "ping":
        if _ws_connection:
            await _ws_connection.send(json.dumps({"type": "pong"}))

    elif msg_type == "error":
        log(f"❌ Server error: {data.get('message', '')}")


def _show_os_notification(title: str, body: str):
    """Show a native OS notification."""
    try:
        import platform
        system = platform.system()
        if system == "Darwin":
            os.system(f'osascript -e \'display notification "{body}" with title "{title}"\'')
        elif system == "Windows":
            try:
                from plyer import notification
                notification.notify(title=title, message=body, app_name="IRIS AI", timeout=5)
            except ImportError:
                pass
        elif system == "Linux":
            os.system(f'notify-send "{title}" "{body}"')
    except Exception:
        pass


# ─── Main WebSocket Loop ──────────────────────────────────────────────────────
async def connect_and_run():
    """Main connection loop with exponential backoff reconnection."""
    global _ws_connection, _running
    retry = 0

    while _running:
        url = f"{SERVER_WS_URL}/ws/{DEVICE_ID}?token={AUTH_TOKEN}"
        log(f"Connecting to {SERVER_WS_URL}...")

        try:
            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
            ) as ws:
                _ws_connection = ws
                retry = 0
                log("WebSocket connected!")

                # Start telemetry loop
                telemetry_task = asyncio.create_task(telemetry_loop(ws))

                # Listen for messages
                async for message in ws:
                    await handle_message(message)
                    if not _running:
                        break

                telemetry_task.cancel()

        except websockets.exceptions.ConnectionClosedOK:
            log("Connection closed cleanly.")
        except websockets.exceptions.ConnectionClosedError as e:
            log(f"Connection closed with error: {e}")
        except ConnectionRefusedError:
            log("Connection refused. Is the IRIS server running?")
        except Exception as e:
            log(f"Connection error: {e}")
        finally:
            _ws_connection = None

        if not _running:
            break

        # Exponential backoff
        wait = min(5 * (2 ** retry), 60)
        retry += 1
        log(f"Reconnecting in {wait}s... (attempt {retry})")
        await asyncio.sleep(wait)


# ─── Entry Point ──────────────────────────────────────────────────────────────
def main():
    global _voice_engine, _running

    if not AUTH_TOKEN or AUTH_TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("=" * 60)
        print("ERROR: IRIS_AUTH_TOKEN not configured!")
        print("1. Register your device at http://localhost:3000/dashboard")
        print("2. Copy the device token to your .env file")
        print("=" * 60)
        sys.exit(1)

    log(f"IRIS Desktop Agent starting on device '{DEVICE_ID}'")

    # ── Voice Engine ─────────────────────────────────────────────────────────
    if ENABLE_VOICE:
        try:
            _voice_engine = VoiceEngine()
            _voice_engine.speak("IRIS online. How can I help you?")
            _voice_engine.start_continuous_listening(voice_command_callback)
            log("Voice engine started. Say 'Hey IRIS' to activate.")
        except Exception as e:
            log(f"Voice engine failed to start: {e}")
            _voice_engine = None

    # ── System Tray ──────────────────────────────────────────────────────────
    if ENABLE_TRAY:
        def tray_connect():
            log("Reconnect requested from tray")

        def tray_disconnect():
            global _running
            log("Disconnect requested from tray")

        def tray_quit():
            global _running
            _running = False
            sys.exit(0)

        tray_thread = threading.Thread(
            target=create_tray_icon,
            args=(tray_connect, tray_disconnect, tray_quit, lambda: "online"),
            daemon=True,
        )
        tray_thread.start()

    # ── Graceful Shutdown ────────────────────────────────────────────────────
    def shutdown(sig=None, frame=None):
        global _running
        log("Shutting down IRIS agent...")
        _running = False
        if _voice_engine:
            _voice_engine.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ── Run ──────────────────────────────────────────────────────────────────
    asyncio.run(connect_and_run())


if __name__ == "__main__":
    main()
