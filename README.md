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

## 📊 Current Project Progress

| Phase | Status | Milestone Description |
| :--- | :---: | :--- |
| **Phase 1** | ✅ Completed | Foundation, Authentication, Q&A, Voting, Points & Leaderboard |
| **Phase 2** | ✅ Completed | Community, Student Profiles, Study Groups, Connections & Real-Time DM |
| **Phase 3** | ✅ Completed | Nearby Study Discovery, Interactive Map, Storage Abstraction & Requests |
| **Phase 4** | ⏳ Pending | Productivity (Pomodoro Timer, Group Sessions & Study Goals) |
| **Phase 5** | ⏳ Pending | Production Polish, Performance Tuning & Deployment |

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

### Frontend
- **Bootstrap 5**: Responsive layout grid and UI component framework
- **Jinja2**: Server-side HTML templating engine
- **Leaflet.js**: Mobile-friendly interactive mapping library
- **JavaScript (ES6+)**: Dynamic client-side interactivity and AJAX workflows
- **HTML5 & CSS3**: Custom dark glassmorphism design system (`#111110` & `#EA8528`)

### Infrastructure
- **Redis GEO**: In-memory spatial indexing and radius calculation engine
- **Socket.IO**: Real-time event transport protocol
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
- ✅ Personal Pomodoro Timer Engine with HTML5 Desktop Notifications & Custom Durations
- ✅ Synchronized Group Focus Rooms via Socket.IO with Role-Based Moderator Controls
- ✅ Automatic +2 Points Awarded per Completed Focus Session & Streak Integration
- ✅ Daily & Weekly Study Goal Tracking with Auto-Calculated Progress Bars
- ✅ High-Performance Aggregated Analytics Dashboard with 5-Minute Redis Caching
- ✅ Chart.js Interactive Graphs for Weekly Hours & Subject Distribution
- ✅ GitHub-Style 365-Day Dark/Amber Contribution Calendar Heatmap

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
| `SECRET_KEY` | Flask signing key (required) |
| `DATABASE_URL` | Leave empty for SQLite dev, or set PostgreSQL URL |
| `REDIS_URL` | Leave empty for in-memory cache / memory spatial fallback |
| `MAIL_*` | SMTP credentials for email verification |
| `MAIL_SUPPRESS_SEND` | Set 1 to print verification emails directly to console |

### 3. Initialize database and run

    flask db upgrade
    python run.py

App runs locally at `http://localhost:5000`

---

## Production

1. Set `FLASK_ENV=production` and a strong, cryptographic `SECRET_KEY`
2. Configure a PostgreSQL `DATABASE_URL` instance
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

## 🚀 Future Roadmap

### Phase 5 — Production Polish
- **Notifications**: Centralized notification bell for upvotes, group activity, and requests.
- **Full-Text Search**: High-performance indexing for instantaneous query discovery.
- **Mobile Optimization**: Refined touch targets and responsive navigation drawers.
- **Performance Improvements**: CDN integration, asset bundling, and database query tuning.
- **Production Deployment**: Docker containerization and cloud orchestration setup.

---

## License

MIT © StudyConnect Team
