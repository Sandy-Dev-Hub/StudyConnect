# StudyConnect

**A student Q&A platform built with Flask.**
Ask doubts, share knowledge, earn points, and climb the leaderboard.

---

## Overview

StudyConnect is a gamified peer-learning community for students preparing for competitive exams (JEE, NEET, UPSC, etc.).

**Phase 1 features:**
- User registration, login, email verification, and password reset
- Ask questions with subject/exam tags and optional image attachments
- Markdown answers with live preview
- Upvote / downvote answers (AJAX)
- Accept best answer (AJAX)
- Points: +10 post, +5 upvote, +25 accept
- Daily login streak tracking
- Leaderboard (all-time and weekly, filterable by subject/exam)
- Search and filter questions
- Responsive glassmorphism UI

---

## Installation

### 1. Clone and install

    git clone <repo-url>
    cd StudyConnect
    python -m venv venv
    venv\Scriptsctivate
    pip install -r requirements.txt

### 2. Configure environment

    cp .env.example .env

Edit .env. Key variables:

| Variable | Description |
|----------|-------------|
| SECRET_KEY | Flask signing key (required) |
| DATABASE_URL | Leave empty for SQLite dev, or set PostgreSQL URL |
| REDIS_URL | Leave empty for in-memory cache |
| MAIL_* | SMTP credentials for email verification |
| MAIL_SUPPRESS_SEND | Set 1 to print emails to console |

### 3. Initialize database and run

    flask db upgrade
    python run.py

App runs at http://localhost:5000

---

## Production

1. Set FLASK_ENV=production and a strong SECRET_KEY
2. Configure PostgreSQL DATABASE_URL
3. Set real SMTP credentials and MAIL_SUPPRESS_SEND=0
4. Run: gunicorn -w 4 -b 0.0.0.0:8000 run:app

---

## Points System

| Action | Points |
|--------|--------|
| Post an answer | +10 |
| Answer accepted | +25 |
| Receive upvote | +5 |
| Receive downvote | -2 |

---

## License

MIT
