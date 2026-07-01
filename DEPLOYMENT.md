# 🚀 StudyConnect v1.0 Production Deployment Guide

This document outlines the step-by-step instructions for deploying **StudyConnect v1.0** to production environments. StudyConnect is built on a modern, highly scalable architecture featuring **Python 3.11+ / Flask**, **SQLAlchemy 2.0**, **Neon Managed PostgreSQL**, **Redis Caching**, and **Flask-SocketIO real-time WebSockets**.

---

## 🏛️ System Architecture

```
[ Client Browser / Mobile App ]
             │
             ▼ (HTTPS / WSS)
   [ Load Balancer / Proxy ]
             │
             ▼
[ Gunicorn + Gevent Workers ] ──► [ Redis 7 Cache & Pub/Sub ]
             │
             ▼
[ Neon Cloud PostgreSQL (Serverless) ]
```

### Key Architectural Guidelines
1. **Managed Database**: Do not run local PostgreSQL instances in containers. Connect directly to **Neon Managed Cloud PostgreSQL** (`postgresql://...`) via environment variables.
2. **Real-Time WebSockets**: Gunicorn must use the **Gevent** worker class (`worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"`) to handle concurrent WebSockets and background tasks cleanly.
3. **Caching & Notification Queues**: Redis (`redis://...`) stores 5-minute leaderboards, analytics memoization, live search queries, and Socket.IO Pub/Sub messaging.

---

## 🔑 Required Environment Variables

Configure these environment variables in your deployment platform:

| Variable | Required | Default / Example | Description |
| :--- | :---: | :--- | :--- |
| `FLASK_APP` | Yes | `run.py` | Entrypoint file for Flask |
| `FLASK_ENV` | Yes | `production` | Production environment flag |
| `SECRET_KEY` | Yes | *64-char hex string* | Cryptographic signing key for sessions/tokens |
| `DATABASE_URL` | Yes | `postgresql://user:pass@ep-host.neon.tech/neondb` | Neon PostgreSQL Serverless Connection URI |
| `REDIS_URL` | Yes | `redis://redis-host:6379/0` | Redis caching & WebSocket adapter URL |
| `GUNICORN_WORKERS` | No | `4` | Number of worker processes |
| `MAIL_SERVER` | Optional | `smtp.gmail.com` | SMTP host for email notifications |
| `MAIL_PORT` | Optional | `587` | SMTP port |
| `MAIL_USERNAME` | Optional | `admin@studyconnect.com` | SMTP authentication email |
| `MAIL_PASSWORD` | Optional | `app-specific-password` | SMTP authentication password |

---

## 🐳 Option 1: Docker Compose (VMs / Dedicated Servers / AWS EC2)

StudyConnect includes an optimized multi-stage `Dockerfile` and `docker-compose.yml` for effortless deployment on any Linux VM.

### 1. Clone & Configure Environment
```bash
git clone https://github.com/your-org/StudyConnect.git
cd StudyConnect

# Create environment file
cat <<EOF > .env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://neondb_owner:password@ep-example.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
EOF
```

### 2. Build & Launch Containers
```bash
docker-compose up -d --build
```

### 3. Run Database Migrations
```bash
docker exec -it studyconnect_web flask db upgrade
```

### 4. Verify Application Health
```bash
curl http://localhost:5000/api/health
```
**Expected Output:**
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "socketio": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-30T12:00:00Z"
}
```

---

## ☁️ Option 2: Render / Railway Deployment

### Render.com Setup
1. Create a new **Web Service** connected to your GitHub repository.
2. Select **Docker** as the Runtime.
3. In the Environment section, add your `DATABASE_URL` (Neon PostgreSQL) and `REDIS_URL` (Render Redis instance).
4. Set the Health Check Path to `/api/health`.

### Railway.app Setup
1. Create a new Project and deploy from GitHub repo.
2. Add a **Redis** service within the Railway canvas.
3. In your Web app service variables, reference `${{Redis.REDIS_URL}}` and set `DATABASE_URL` to your Neon PostgreSQL connection string.

---

## 🛡️ Production Security & Monitoring

StudyConnect v1.0 automatically enforces enterprise security measures in production:
- **HTTP Security Headers**: Automatically applies `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **Query & Latency Monitoring**: Loggers track all requests taking `> 500ms` and database queries exceeding `100ms` for immediate diagnostics.
- **Cache Hit Optimization**: Static assets receive 7-day browser caching while dynamic API search suggestions are cached in Redis for 30 seconds.
