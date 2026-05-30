# IRIS AI 
### Intelligent Responsive Integrated System

> A cross-platform personal AI assistant inspired by JARVIS. Control all your devices, chat with a context-aware LLM, manage tasks, and receive unified notifications — from a single futuristic command center.

---

## Architecture

```
IRIS AI
├── backend/              FastAPI + PostgreSQL + Redis + ChromaDB
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/     auth, chat, devices, tasks, memory, ws
│   │   ├── core/              config, security, database
│   │   ├── models/            SQLAlchemy 2.x models
│   │   ├── services/          LLM, memory, automation, notifications
│   │   └── websockets/        connection manager
│   └── Dockerfile
│
├── clients/
│   ├── web/              Next.js 16 + Tailwind v4 — JARVIS HUD Dashboard
│   ├── desktop-agent/    Python — macOS/Windows/Linux agent
│   └── mobile/           Flutter — Android companion app
│
├── deployment/           Docker Compose
└── docs/                 Setup guide, API docs
```

---

## Features

| Feature | Status |
|---------|--------|
| LLM Chat (streaming) | ✅ |
| Voice commands (Web STT) | ✅ |
| Text-to-speech (TTS) | ✅ |
| Wake word detection | ✅ |
| Device control (lock/sleep/volume/brightness) | ✅ |
| Open/close apps | ✅ |
| Browser control | ✅ |
| Screenshot | ✅ |
| File search | ✅ |
| WhatsApp via Web | ✅ |
| Real-time telemetry (CPU/RAM/Disk/Battery) | ✅ |
| Task management | ✅ |
| Notes (planned) | 🔄 |
| Long-term memory (ChromaDB) | ✅ |
| Multi-device support | ✅ |
| JWT auth + refresh tokens | ✅ |
| System tray icon | ✅ |
| Browser notifications | ✅ |
| Docker deployment | ✅ |

---

## Quick Start

**Option A: Local (development)**
```bash
# See docs/SETUP.md for detailed instructions
```

**Option B: Docker Compose (production)**
```bash
cd deployment
cp ../backend/.env.example ../backend/.env
# Edit ../backend/.env

docker compose up -d
```

- Backend API: http://localhost:8000/api/v1/docs
- Web Dashboard: http://localhost:3000
- Metrics: http://localhost:8000/health

---

## AI Provider

IRIS uses **free LLM models via OpenRouter**.

1. Sign up at https://openrouter.ai (free)
2. Get your API key
3. Add to `backend/.env`:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

Default model: `deepseek/deepseek-chat-v3-0324:free`  
Fallbacks: `google/gemma-3-27b-it:free`, `mistralai/mistral-7b-instruct:free`

---

## WebSocket Protocol

See [docs/WEBSOCKET_EVENTS.md](docs/WEBSOCKET_EVENTS.md) for the full protocol reference.

---

## API Reference

Interactive docs at: http://localhost:8000/api/v1/docs

| Endpoint | Description |
|----------|-------------|
| `POST /auth/register` | Create account |
| `POST /auth/login` | Get JWT tokens |
| `POST /auth/refresh` | Refresh access token |
| `GET /auth/me` | Current user |
| `POST /chat/` | Send message to IRIS |
| `GET /chat/conversations` | Conversation history |
| `POST /devices/register` | Register device |
| `GET /devices/` | List devices |
| `POST /devices/{id}/command` | Send command to device |
| `CRUD /productivity/tasks` | Task management |
| `CRUD /productivity/notes` | Notes management |
| `GET /memory/search` | Search long-term memory |
| `WS /ws/{device_id}` | Real-time device connection |

---

## Voice Commands

| Say... | IRIS Does |
|--------|-----------|
| "Lock my screen" | Locks computer |
| "Turn volume up" | Increases volume |
| "Open YouTube" | Opens YouTube in browser |
| "Set brightness to 50%" | Adjusts display brightness |
| "Take a screenshot" | Captures screen |
| "Open Spotify" | Launches Spotify |
| "Remind me to call mom" | Creates a reminder |
| "What are my tasks?" | Lists pending tasks |
| "Send WhatsApp to John: I'll be late" | Sends WhatsApp message |

---

## Security

- JWT access tokens (15 min expiry) + refresh tokens (7 days)
- Fernet-encrypted sensitive data in database
- Per-user memory isolation in ChromaDB
- Non-root Docker users
- CORS configured per environment

---

## License

MIT License — Personal use only. Do not expose publicly without securing all endpoints.
