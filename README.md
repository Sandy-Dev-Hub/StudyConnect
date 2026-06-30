# ⚡ StudyConnect

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![Socket.io](https://img.shields.io/badge/Socket.io-Real--Time-010101?style=for-the-badge&logo=socket.io&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Geospatial-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-ORM-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-Maps-199900?style=for-the-badge&logo=leaflet&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-EA8528?style=for-the-badge)

**A gamified peer-learning community, collaborative study platform, and real-time networking ecosystem built with Flask.**
Ask doubts, share knowledge, earn points, climb the leaderboard, form collaborative study groups, and discover peers studying near you.

---

## Overview

StudyConnect is a gamified peer-learning community for students preparing for competitive exams (JEE, NEET, UPSC, SAT, GRE, etc.).

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

## 🚀 Phase 2 — Community & Networking

Phase 2 introduces vibrant social networking and real-time collaboration tools. **Crucially, Phase 2 was implemented while preserving every Phase 1 feature and maintaining the premium dark glassmorphism design language (#111110 background, #EA8528 amber accent).**

### Study Groups
- Create public and private study groups tailored to specific subjects and exams
- Join and leave study groups dynamically
- Complete group management features for administrators
- Granular group member roles (Owner, Moderator, Member)
- Real-time group activity feeds and shared discussion questions
- Subject & exam based group categorization

### Student Profiles
- Custom avatar image uploads with dynamic fallback rendering
- High-resolution profile banners
- Personalized student bios
- Subject specialization badges
- Exam specialization tracking
- Comprehensive statistics dashboards displaying:
  - Total earned points
  - Daily login and study streaks
  - Total questions answered
  - Total questions asked

### Student Connections
- Send direct connection requests to fellow peers
- Accept / Reject incoming requests with real-time feedback
- Dedicated connections network list
- Discovery of mutual connections between students

### Real-Time Messaging
- Private 1-on-1 direct messaging powered by **Flask-SocketIO** and **Redis Pub/Sub**
- Live typing indicators (`User is typing...`)
- Real-time online status tracking and presence updates
- Instant message delivery and read receipts
- Ergonomic split-screen chat UI with sidebar conversation switcher
- Fully responsive messaging interface optimized for all screen sizes

---

## 🌍 Phase 3 — Nearby Study Discovery

Phase 3 transforms StudyConnect into a location-aware study companion, allowing students to discover peers studying nearby and initiate real-time collaboration sessions safely. **All existing Phase 1 and Phase 2 functionality remains fully compatible.**

### Location Sharing
- Powered by the browser Geolocation API
- Strict opt-in location sharing model
- Manual start and stop sharing controls
- Automatic expiration after 4 hours of inactivity
- Temporary Redis geospatial storage
- **Never permanently stores GPS coordinates** in any relational database

### Privacy & Security
- **Randomized coordinate jitter** ($\pm 0.0005$) applied before approximation
- Approximate locations only ($\sim 100\text{m} - 150\text{m}$ accuracy rounding to 3 decimal places)
- Exact GPS coordinates are never exposed to the client or network API
- Automatic cleanup of background data upon session timeout
- Immediate location broadcast termination on logout or SocketIO disconnect

### Nearby Discovery
- Interactive map powered by **Leaflet.js** and **CartoDB Dark Matter tiles** matching the dark theme
- Custom glowing amber avatar map markers
- Discover nearby students within a configurable radius ($1\text{km}$, $2\text{km}$, $5\text{km}$, $10\text{km}$)
- Dynamic filtering by Subject specialization
- Dynamic filtering by Exam specialization
- Sorting by Distance (Nearest), Study Streak, or Total Points
- Responsive discovery panel and active peer sidebar

### Study Requests
- Send instant study invitations to peers appearing on the nearby map
- Accept or Reject requests via real-time modal drawers
- Anti-spam **30-second cooldown** enforced between requests
- Duplicate pending request prevention logic
- Automatic request expiration after 15 minutes

### Real-Time Integration
- Instant **Socket.IO events** (`study_request_received`, `study_request_accepted`, `study_request_rejected`)
- Live nearby feed updates reflecting peer movement or status changes
- Instant toast notifications across all active tabs
- **Automatic private chat creation**: Accepting a request invokes Phase 2's `Conversation.get_or_create()` and immediately redirects both users into a live messaging session

### Enterprise Features
- **Redis GEO indexing** (`GEOADD`, `GEOSEARCH`, `GEODIST`) for high-concurrency spatial queries
- Thread-safe **Memory fallback** (`MemoryLocationStorage`) for local Windows and development environments
- API rate limiting decorators (`@rate_limit`) protecting discovery endpoints
- Structured JSON logging across all spatial events
- Centralized exception handling ensuring graceful error recovery
- Storage abstraction architecture (`get_storage()`)
- Anonymous analytics hooks tracking platform adoption metrics

---

## ⏱ Phase 4 — Productivity & Study Analytics

Phase 4 introduces powerful productivity tools, study tracking, and personal analytics designed to keep students focused and motivated. **All existing Phase 1, Phase 2, and Phase 3 functionality remains fully integrated and operational.**

### ⏱ Personal Pomodoro
- Focus timer with start, pause, resume, and reset controls
- Custom durations tailored to individual study habits
- HTML5 Browser notifications on session completion
- Auto-save sessions and persistent state tracking across browser refreshes
- Session persistence backed by user activity logs
- **+2 points** awarded automatically on completed focus sessions
- Automatic daily study streak updates upon session completion

### 👥 Group Pomodoro
- Shared study rooms for synchronized peer focus
- Real-time synchronized timers across all connected participants
- **Socket.IO synchronization** ensuring instantaneous state broadcast
- **Redis-backed timer persistence** preventing state drift
- Granular Moderator/Admin controls to start, pause, and reset group timers
- Live synchronized countdown visible to all members in the room

### 🎯 Study Goals
- Daily goals tracking study targets
- Weekly goals tracking cumulative progress
- Intuitive goal creation and management
- Automated goal completion tracking
- Animated progress bars reflecting real-time percentage completion

### 📊 Productivity Dashboard
- Comprehensive weekly study hours tracking
- Visual subject breakdown showing time spent per topic
- Dynamic goal completion rate calculation
- GitHub-style 365-day dark/amber contribution heatmap
- Interactive **Chart.js** analytics and distribution charts
- Granular study session history logs

---

## 🔍 Phase 5 — Production Polish & Enterprise Features

Phase 5 elevates StudyConnect into a high-performance, enterprise-grade application ready for public deployment on modern cloud platforms.

### 🔍 Phase 5B — PostgreSQL Search Engine
- **Generated TSVector Columns**: Automated vector synchronization via PostgreSQL dialect DDL (`GENERATED ALWAYS AS (...) STORED`).
- **GIN Indexing**: Inverted index creation across all searchable text columns for sub-millisecond query lookups.
- **Relevance Ranking (`ts_rank`)**: Intelligent result ordering based on term frequency and matching density.
- **Highlighted Excerpts (`ts_headline`)**: Dynamic `<mark>` HTML wrapping around matching search terms.
- **Prefix Matching**: Prefix query support (`to_tsquery('english', 'term:*')`) allowing rapid partial-word autocomplete.
- **Categorized Suggestions**: Interactive floating navbar search delivering structured split results for Questions and Study Groups.

---

## 📸 Screenshots & Placeholders

### Productivity Dashboard
```
[ Screenshot Placeholder: Productivity Dashboard Overview ]
```

### Pomodoro Timer
```
[ Screenshot Placeholder: Personal Focus Pomodoro Timer ]
```

### Group Focus Room
```
[ Screenshot Placeholder: Synchronized Group Focus Room ]
```

### Study Goals
```
[ Screenshot Placeholder: Daily & Weekly Study Goals ]
```

### Analytics Dashboard
```
[ Screenshot Placeholder: Chart.js Analytics & Subject Breakdown ]
```

### Heatmap
```
[ Screenshot Placeholder: GitHub-Style Contribution Heatmap ]
```

---

## 📊 Current Project Progress

| Phase | Status | Milestone Description |
| :--- | :---: | :--- |
| **Phase 1** | ✅ Completed | Foundation, Authentication, Q&A, Voting, Points & Leaderboard |
| **Phase 2** | ✅ Completed | Community, Student Profiles, Study Groups, Connections & Real-Time DM |
| **Phase 3** | ✅ Completed | Nearby Study Discovery, Interactive Map, Storage Abstraction & Requests |
| **Phase 4** | ✅ Completed | Productivity (Pomodoro Timer, Group Sessions & Study Goals) |
| **Phase 5** | 🚧 In Progress | Enterprise FTS Search Engine (Completed), Notifications, Performance & Deployment |

---

## 🛠 Technology Stack

### Backend
- **Flask**: Lightweight Python web framework
- **Flask-SocketIO**: WebSockets and real-time bi-directional communication
- **SQLAlchemy**: Object-Relational Mapping (ORM)
- **PostgreSQL**: Robust production relational database
- **Redis**: High-speed in-memory data store & Pub/Sub broker
- **GeoAlchemy2**: Spatial database extension schemas
- **Alembic / Flask-Migrate**: Database schema migration management
- **Productivity Blueprint**: Dedicated modular structure for focus sessions and goals
- **Analytics Service**: High-performance aggregation engine with Redis caching

### Frontend
- **Bootstrap 5**: Responsive layout grid and UI component framework
- **Jinja2**: Server-side HTML templating engine
- **Leaflet.js**: Mobile-friendly interactive mapping library
- **Chart.js**: Interactive data visualization and study graphs
- **Pomodoro Engine**: Client-side background timer with HTML5 notifications
- **Heatmap Components**: GitHub-style activity contribution matrix
- **JavaScript (ES6+)**: Dynamic client-side interactivity and AJAX workflows
- **HTML5 & CSS3**: Custom dark glassmorphism design system (`#111110` & `#EA8528`)

### Infrastructure
- **Redis GEO**: In-memory spatial indexing and radius calculation engine
- **Redis Timer Persistence**: Reliable shared room state and countdown storage
- **Socket.IO Synchronization**: Low-latency WebSocket event broadcasting
- **Gunicorn**: WSGI HTTP server for production deployment
- **Eventlet**: Concurrent networking library for WebSocket support

---

## ✨ Key Features

### Foundation & Community (Phases 1 & 2)
- ✅ User Registration, Email Verification & Password Reset
- ✅ Rich Markdown Question & Answer Engine with Image Attachments
- ✅ AJAX Upvoting, Downvoting, and Best Answer Acceptance
- ✅ Gamified Points System & Daily Login Streaks
- ✅ Global & Weekly Filterable Leaderboards
- ✅ Public & Private Study Groups with Role Management
- ✅ Customizable Student Profiles with Avatars, Banners & Bios
- ✅ Peer Networking & Connection Requests
- ✅ Real-Time Split-Screen Direct Messaging with Typing Indicators

### Nearby Discovery & Collaboration (Phase 3)
- ✅ Browser Geolocation Opt-In Location Sharing
- ✅ Privacy-First Randomized Jitter ($\pm 0.0005$) & 3 Decimal Rounding
- ✅ Interactive Leaflet Map with CartoDB Dark Matter Tiles
- ✅ Custom Glowing Amber Avatar Map Markers
- ✅ Configurable Radius Search ($1\text{km} - 10\text{km}$) with Subject/Exam Filters
- ✅ Instant Study Requests with 30s Cooldown & Anti-Spam Protection
- ✅ Real-Time Socket.IO Invitation Notifications & Drawer Modal

### Productivity & Study Analytics (Phase 4)
- ✅ Personal Pomodoro
- ✅ Group Pomodoro
- ✅ Daily & Weekly Goals
- ✅ Productivity Dashboard
- ✅ Analytics
- ✅ Heatmap
- ✅ Study Session Tracking

### Future Polish (Phase 5)
- 🚧 Global Real-Time Push Notifications (Coming Soon)
- 🚧 Full-Text Elasticsearch Question & Group Search (Coming Soon)
- 🚧 Progressive Web App (PWA) Mobile Optimization (Coming Soon)

---

## Installation

### 1. Clone and install

    git clone <repo-url>
    cd StudyConnect
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

### 2. Configure environment

    cp .env.example .env

Edit `.env`. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask signing key (required for secure sessions) |
| `DATABASE_URL` | Leave empty for SQLite dev, or provide a Neon / PostgreSQL connection string (`postgresql+psycopg://...`) |
| `REDIS_URL` | Provide a Redis instance URL (`redis://...`) for spatial queries and room sync, or leave empty for in-memory fallback |
| `MAIL_*` | SMTP credentials for email verification |
| `MAIL_SUPPRESS_SEND` | Set `1` to print verification emails directly to console |

#### ☁️ Neon PostgreSQL Setup
To connect StudyConnect to a serverless **Neon PostgreSQL** production database:
1. Create a project on [Neon](https://neon.tech) and copy your connection string.
2. In your `.env` file, set `DATABASE_URL=postgresql+psycopg://user:pass@ep-xyz.region.aws.neon.tech/dbname?sslmode=require`.
3. Run `flask db upgrade` to automatically execute all Alembic schema migrations against Neon.

#### 🔴 Redis Setup
To enable high-performance spatial indexing (GeoAlchemy/Redis GEO) and real-time synchronized Pomodoro timer persistence:
1. Install and start a local Redis server or provision a cloud instance (e.g., Redis Cloud / Upstash).
2. In your `.env` file, set `REDIS_URL=redis://localhost:6379/0` (or your cloud broker URI).

### 3. Initialize database and run

    flask db upgrade
    python run.py

App runs locally at `http://localhost:5000`

---

## Production

1. Set `FLASK_ENV=production` and a strong, cryptographic `SECRET_KEY`
2. Configure a serverless Neon PostgreSQL `DATABASE_URL` instance
3. Set real SMTP server credentials and `MAIL_SUPPRESS_SEND=0`
4. Configure `REDIS_URL` for production WebSocket Pub/Sub and GEO indexing
5. Run using Eventlet worker class: `gunicorn -k eventlet -w 1 -b 0.0.0.0:8000 run:app`

---

## Points System

| Action | Points Earned |
|---|:---:|
| Post an answer | **+10** |
| Answer accepted | **+25** |
| Receive upvote | **+5** |
| Receive downvote | **-2** |
| Complete focus study session | **+2** |

---

## 🚀 Phase 5 — Production Polish & Enterprise Features (v1.0.0 Production Ready)

### ✅ Phase 5A — PostgreSQL Full Text Search Engine
- **Enterprise FTS:** Powered by PostgreSQL `TSVECTOR` and GIN indexing on `Question` and `StudyGroup` models.
- **Relevancy Scoring & Excerpts:** Uses `ts_rank` for relevancy matching and `ts_headline` with `<mark>` tags for dynamic excerpt highlighting.
- **Floating Autocomplete:** Live dropdown search results across questions and study groups.

### ✅ Phase 5B — Real-Time Notification System
- **Centralized Hub:** Dedicated Notification bell in navbar with animated red unread badge pill and glassmorphic dropdown.
- **Real-Time Delivery:** Instantaneous Socket.IO broadcasting (`new_notification`) with floating Bootstrap toasts.
- **Universal Event Hooks:** Automated notifications for Q&A answers, accepted answers, connection requests, group joins, nearby study matches, pomodoro completions, and study streak increases.
- **Notification History Page:** Comprehensive filtering and management page at `/notifications`.

### ✅ Phase 5C — Performance Optimization
- **Intelligent Redis Caching:** 5-minute memoization on leaderboards and home stats, 5-minute cache on user analytics dashboards, and 30-second cache on live search suggestions.
- **Zero N+1 Queries:** Eager loading (`joinedload()`) integrated across feeds, profile views, groups, notifications, and productivity models.
- **Query & Latency Logging:** Automatic threshold monitoring logging slow database queries (`> 100ms`) and HTTP requests (`> 500ms`).

### ✅ Phase 5D — Responsive UI & Accessibility (WCAG 2.1 AA)
- **Flawless Responsiveness:** Zero horizontal scrolling across standard viewports (1920px down to 360px mobile viewports).
- **Universal Touch Targets:** Minimum `44×44px` clickable dimensions enforced across all buttons, dropdown items, and navigation links on mobile devices.
- **High-Contrast Design:** Upgraded secondary text opacity (`--text-2: 0.68`) ensuring `> 4.5:1` contrast ratios on dark backgrounds.
- **Keyboard Navigation:** High-visibility amber `:focus-visible` outlines and ARIA combobox/navigation labels.

### ✅ Phase 5E — Production Deployment & Cloud Orchestration
- **Production Containerization:** Optimized multi-stage `Dockerfile` running non-root runtime user (`studyconnect`).
- **Cloud Database Ready:** Zero local DB containers in `docker-compose.yml`; natively connects to serverless **Neon Managed PostgreSQL**.
- **Real-Time Eventlet Workers:** Production `gunicorn_config.py` configured with Eventlet async workers for seamless Socket.IO WebSocket handling.
- **Health Diagnostics:** Built-in `GET /api/health` endpoint monitoring live DB, Redis, and Socket.IO status.
- **Deployment Guide:** Comprehensive deployment documentation in `DEPLOYMENT.md`.

---

## License

MIT © StudyConnect Team

