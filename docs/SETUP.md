# IRIS AI — Local Development Setup Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend |
| Node.js | 20+ | Web dashboard |
| PostgreSQL | 16+ | Database |
| Redis | 7+ | Cache/queuing |
| Flutter | 3.22+ | Android app (optional) |

---

## Step 1: Clone / Open Project

```bash
cd ~/Desktop/IRIS\ AI
```

---

## Step 2: Backend Setup

### 2a. Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set:
```
# Required:
OPENROUTER_API_KEY=sk-or-v1-...   # Get free at openrouter.ai
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(64))">
ENCRYPTION_KEY=<generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
```

### 2b. Start PostgreSQL

**macOS (Homebrew):**
```bash
brew services start postgresql@16
createdb iris_db
createuser iris -P  # password: iris_pass
psql -c "GRANT ALL PRIVILEGES ON DATABASE iris_db TO iris;"
```

**Docker (easiest):**
```bash
docker run -d \
  --name iris-postgres \
  -e POSTGRES_USER=iris \
  -e POSTGRES_PASSWORD=iris_pass \
  -e POSTGRES_DB=iris_db \
  -p 5432:5432 \
  postgres:16-alpine
```

### 2c. Start Redis

**macOS:**
```bash
brew services start redis
```

**Docker:**
```bash
docker run -d --name iris-redis -p 6379:6379 redis:7-alpine
```

### 2d. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# OR: venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 2e. Start the Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend is running at: http://localhost:8000  
📖 API docs: http://localhost:8000/api/v1/docs

---

## Step 3: Web Dashboard Setup

```bash
cd clients/web

# Create environment file
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > .env.local
echo 'NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1' >> .env.local

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ Dashboard is running at: http://localhost:3000

---

## Step 4: Register Your First Account

1. Open http://localhost:3000
2. Click **[ REGISTER ]**
3. Enter email + password
4. Click **[ AUTHENTICATE ]** to log in

---

## Step 5: Desktop Agent Setup

```bash
cd clients/desktop-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
```

**Get your device token:**
1. Log into the dashboard at http://localhost:3000
2. In the Devices panel, click **↻ Refresh**
3. Use the API: `POST /api/v1/devices/register`
   ```bash
   curl -X POST http://localhost:8000/api/v1/devices/register \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"device_name": "desktop-main", "device_type": "macos"}'
   ```
4. Copy the `auth_token` from the response into `.env`

**Start the agent:**
```bash
python agent.py
```

---

## Step 6: macOS Permissions (Required!)

The desktop agent needs these permissions in:
**System Settings → Privacy & Security**

| Permission | Required For |
|-----------|-------------|
| Microphone | Voice commands |
| Accessibility | Keyboard/mouse automation |
| Screen Recording | Screenshots |

---

## Step 7: Test Everything

1. Open dashboard → You should see the IRIS orb
2. Your desktop should appear in the Devices panel (online)
3. Type a message like "What's the weather like?" — IRIS responds
4. Try "Hey IRIS, lock my screen" — your Mac should lock

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| `Connection refused` on backend | Check PostgreSQL is running |
| `redis.exceptions.ConnectionError` | Start Redis |
| LLM returns error | Check `OPENROUTER_API_KEY` in `backend/.env` |
| Voice not working | Use Chrome/Edge (Firefox doesn't support Web Speech API) |
| Agent not connecting | Check `IRIS_AUTH_TOKEN` in `desktop-agent/.env` |
| `ModuleNotFoundError` | Make sure venv is activated |
