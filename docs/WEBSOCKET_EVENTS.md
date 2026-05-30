# IRIS AI — WebSocket Protocol Reference

All WebSocket connections go to:
```
ws://<server>/api/v1/ws/{device_id}?token=<jwt>
```

---

## Connection

**device_id**: A unique identifier for the connecting device (e.g., `desktop-main`, `android-pixel8`, `web-dashboard`)  
**token**: JWT access token obtained from `/auth/login`

---

## Message Format

All messages are JSON objects with a required `type` field.

---

## Client → Server Messages

### `voice_command` / `chat_message`
Send a text command or chat message to IRIS.

```json
{
  "type": "voice_command",
  "content": "Hey IRIS, lock my screen",
  "conversation_id": 42  
}
```
- `conversation_id` is optional. Omit to start a new conversation.

---

### `telemetry`
Send system metrics from desktop/mobile to server.

```json
{
  "type": "telemetry",
  "data": {
    "cpu": 45.2,
    "ram": 68.1,
    "disk": 55.0,
    "battery": 87.5,
    "network": 1.4
  }
}
```
- All values are percentages (0-100) except `network` (MB/s)
- Send every 10 seconds

---

### `notification`
Forward a phone/desktop notification to all other devices.

```json
{
  "type": "notification",
  "notification": {
    "title": "WhatsApp",
    "body": "John: Hey, you there?",
    "notification_type": "info"
  }
}
```
- `notification_type`: `"info"` | `"warning"` | `"error"` | `"reminder"`

---

### `command_result`
Send the result of an executed device command back to server.

```json
{
  "type": "command_result",
  "result": {
    "success": true,
    "action": "lock_screen"
  }
}
```

---

### `pong`
Response to server ping (heartbeat).
```json
{ "type": "pong" }
```

---

## Server → Client Messages

### `connected`
Sent immediately after successful connection.

```json
{
  "type": "connected",
  "device_id": "desktop-main",
  "user_id": 1,
  "message": "Connected to IRIS Central Server"
}
```

---

### `llm_chunk`
Streaming text delta from the LLM response.

```json
{
  "type": "llm_chunk",
  "content": "Of course! I'll",
  "conversation_id": 42
}
```
- Clients should append chunks to build the full response.
- Followed by a `llm_response` message when complete.

---

### `llm_response`
Final complete LLM response (after all chunks are sent).

```json
{
  "type": "llm_response",
  "content": "Of course! I'll lock your screen now.",
  "conversation_id": 42,
  "intent": "lock_screen",
  "command": {
    "action": "lock_screen",
    "params": {}
  }
}
```

---

### `command`
A device control command dispatched from the server.

```json
{
  "type": "command",
  "data": {
    "action": "set_volume",
    "level": 50
  }
}
```

**All supported actions:**

| Action | Params |
|--------|--------|
| `lock_screen` | _(none)_ |
| `sleep` | _(none)_ |
| `shutdown` | _(none)_ |
| `restart` | _(none)_ |
| `open_browser` | `url: string` |
| `open_app` | `name: string` |
| `close_app` | `name: string` |
| `set_volume` | `level: 0-100` |
| `volume_up` | `step: number` |
| `volume_down` | `step: number` |
| `mute` | _(none)_ |
| `set_brightness` | `level: 0-100` |
| `take_screenshot` | _(none)_ |
| `search_files` | `query: string` |
| `type_text` | `text: string` |
| `send_whatsapp` | `contact: string, message: string` |
| `send_sms` | `number: string, message: string` |
| `make_call` | `number: string` |

---

### `device_telemetry`
Broadcast of another device's telemetry (sent to web dashboard).

```json
{
  "type": "device_telemetry",
  "device_id": "desktop-main",
  "data": { "cpu": 45.2, "ram": 68.1, "disk": 55.0 }
}
```

---

### `notification`
Push notification forwarded from another device.

```json
{
  "type": "notification",
  "source_device": "android-pixel8",
  "notification": {
    "title": "Gmail",
    "body": "New email from boss@company.com",
    "notification_type": "info"
  }
}
```

---

### `system_event`
System-level events like device connect/disconnect.

```json
{
  "type": "system_event",
  "event": "device_connected",
  "data": { "device_id": "android-pixel8" }
}
```

Events: `device_connected` | `device_disconnected`

---

### `ping`
Server heartbeat. Client must respond with `pong`.
```json
{ "type": "ping" }
```

---

### `error`
Error message from server.
```json
{
  "type": "error",
  "message": "Auth failed: Invalid token"
}
```

---

## LLM Intent → Action Tags

When IRIS detects a device action in your message, it embeds an action tag in its response:

```
[ACTION:action_name:{"param": "value"}]
```

Examples:
- `[ACTION:lock_screen:{}]`
- `[ACTION:open_browser:{"url": "https://youtube.com"}]`
- `[ACTION:set_volume:{"level": 75}]`

The server parses these tags and dispatches the corresponding `command` message to all connected devices.
