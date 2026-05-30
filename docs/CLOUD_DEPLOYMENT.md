# IRIS AI Cloud Deployment Guide

Follow this guide to deploy your IRIS AI infrastructure to the cloud for free.

## Step 1: Set Up Supabase (PostgreSQL)

1. Go to [Supabase](https://supabase.com/) and create a free account.
2. Click **New Project** and select an organization.
3. Name it `iris-ai-db`, set a strong Database Password, and choose a region close to you.
4. Click **Create new project** (it takes a few minutes to provision).
5. Once ready, go to **Project Settings (gear icon) > Database**.
6. Scroll down to **Connection string** > **URI** and copy the URI.
   - It will look like: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
   - Make sure to replace `[password]` with the actual password you set in step 3.

## Step 2: Set Up Upstash (Redis)

1. Go to [Upstash](https://upstash.com/) and create a free account.
2. Click **Create Database** under the Redis section.
3. Name it `iris-ai-redis`, select the same region as Supabase, and click **Create**.
4. Once created, scroll down to the **Connect to your database** section.
5. Select the **Redis CLI** or **ioredis** tab to find your connection string.
   - It will look like: `rediss://default:[password]@[endpoint]:[port]`
   - Copy this URL.

## Step 3: Set Up Render (FastAPI Backend)

1. Go to [Render](https://render.com/) and create a free account.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub account and select your `IRIS-AI` repository.
4. Fill in the following details:
   - **Name:** `iris-backend`
   - **Root Directory:** `backend` (Important!)
   - **Environment:** `Docker`
   - **Region:** Match your Supabase/Upstash region.
   - **Instance Type:** Free
5. Scroll down to **Environment Variables** and add the following:
   - `DATABASE_URL`: *(Paste your Supabase URI here)*
   - `REDIS_URL`: *(Paste your Upstash URL here)*
   - `OPENROUTER_API_KEY`: *(Your OpenRouter API Key)*
   - `SECRET_KEY`: *(Generate a long random string, e.g., `openssl rand -hex 32`)*
   - `ENCRYPTION_KEY`: *(Generate a Fernet key, e.g., `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)*
   - `ENVIRONMENT`: `production`
6. Click **Create Web Service**.
7. Render will begin building your Docker container. Wait for it to finish and become **Live**.
8. Copy your new Render URL (e.g., `https://iris-backend-xxxx.onrender.com`).

### 3a. Run Database Migrations
Since your remote database is empty, you need to create the tables.
The easiest way is to connect to your Supabase DB locally and run Alembic, or simply wait: the FastAPI lifespan event in `app/main.py` actually calls `Base.metadata.create_all(bind=engine)`, so the tables will automatically create themselves when Render starts up!

## Step 4: Set Up Vercel (Next.js Dashboard)

1. Go to [Vercel](https://vercel.com/) and create a free account.
2. Click **Add New... > Project**.
3. Import your `IRIS-AI` GitHub repository.
4. Fill in the following details:
   - **Project Name:** `iris-ai-dashboard`
   - **Framework Preset:** Next.js
   - **Root Directory:** `clients/web` (Important!)
5. Expand **Environment Variables** and add:
   - `NEXT_PUBLIC_API_URL`: `https://[YOUR_RENDER_URL]/api/v1`
   - `NEXT_PUBLIC_WS_URL`: `wss://[YOUR_RENDER_URL]/api/v1`
6. Click **Deploy**.
7. Once deployed, you will get a public URL for your dashboard (e.g., `https://iris-ai-dashboard.vercel.app`).

## Step 5: Update Your Clients

Now that your brain is in the cloud, point your desktop agent and mobile app to it.

### Desktop Agent (`clients/desktop-agent/.env`)
Update the connection URL to point to your secure WebSocket (`wss://`):
```env
IRIS_SERVER_WS_URL=wss://[YOUR_RENDER_URL]/api/v1
```

### Mobile App (`clients/mobile/lib/services/auth_service.dart`)
Change the base URLs (if you aren't passing them at build time):
```dart
static const String baseUrl = 'https://[YOUR_RENDER_URL]/api/v1';
```

### Mobile App (`clients/mobile/lib/services/websocket_service.dart`)
```dart
static const String wsBaseUrl = 'wss://[YOUR_RENDER_URL]/api/v1';
```

## Step 6: Test!
1. Open your Vercel URL in your browser.
2. Register a new user and login.
3. Start your Desktop Agent. It should connect to the cloud server and appear on your Vercel dashboard!
