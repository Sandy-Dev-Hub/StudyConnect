# StudyConnect

A full-stack social learning and study platform for students to connect, learn, and grow together.

## 🚀 Live Demo

🌐 **[Visit StudyConnect](https://studyconnect-learn.up.railway.app/)**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white)

## 📖 Project Overview

StudyConnect is a comprehensive social learning platform designed to help students collaborate effectively. The platform allows users to:
- Create accounts and build their study profile
- Connect with other students globally
- Ask and answer academic questions
- Participate in dedicated study communities and groups
- Discover nearby study opportunities and peers
- Communicate via direct messages
- Track productivity and study activity
- Earn points, maintain study streaks, and view leaderboards
- Receive notifications for important interactions

## ✨ Main Features

### 🔐 Authentication
- User Registration and Login/Logout
- Secure password handling and hashing
- Flask-Login based session management
- Password reset functionality
- *Note: Email verification infrastructure is built but currently postponed for a future update due to SMTP connectivity restrictions in the Railway environment.*

### ❓ Questions & Answers
- Post academic questions with detailed descriptions
- Answer questions from peers
- Rich text formatting for technical clarity
- Earn points for participating in discussions

### 👥 Community & Connections
- Send and accept connection requests
- View user profiles and mutual connections
- Join or create study groups based on specific subjects
- Participate in group discussions and collaborative learning

### 📍 Nearby Study Discovery
- Discover study opportunities and peers near your location
- Find study spots or groups operating in your local area

### 💬 Real-Time Communication
- WebSocket-based direct messaging using Flask-SocketIO
- Real-time updates for active conversations

### 🏆 Points & Leaderboard
- Gamified learning with a points system for asking/answering questions
- Maintain daily study streaks
- View global leaderboards to compare productivity with peers

### ⏱️ Productivity
- Dedicated productivity tools to track study sessions
- Log study hours and monitor personal progress

### 🔔 Notifications
- Receive alerts for new messages, connection requests, and question replies
- Real-time notification updates across the platform

## 🛠️ Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript, Jinja2 Templates |
| **Backend** | Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Mail, Flask-WTF, Flask-SocketIO |
| **Database** | PostgreSQL (Supabase) |
| **Caching / Real-time** | Redis, Flask-Caching, Socket.IO, Gevent, Gevent-WebSocket |
| **Deployment** | Railway, Docker, Gunicorn |

## 🏗️ Architecture

```mermaid
graph TD
    Client[User Browser] -->|HTTPS / WSS| Railway[Railway Platform]
    Railway --> Web[Flask + Gunicorn / Gevent]
    
    Web -->|Read/Write| DB[(PostgreSQL / Supabase)]
    Web -->|Cache / PubSub| Redis[(Redis)]
    Web -->|Real-time| Sockets[Socket.IO Engine]
```

- **Client:** Users access the platform via standard web browsers.
- **Railway:** Handles SSL termination and routes traffic to the application container.
- **Flask + Gunicorn:** The core Python application serving rendered HTML and handling API logic, using Gevent for asynchronous worker support.
- **PostgreSQL:** Primary relational database hosted on Supabase for persistent data storage.
- **Redis:** In-memory data store used for fast caching (e.g., homepage statistics) and Socket.IO message brokering.

## 📂 Project Structure

```text
StudyConnect/
├── app/
│   ├── answers/          # Answer submission and logic
│   ├── api/              # API endpoints for frontend functionality
│   ├── auth/             # Authentication and user management
│   ├── connections/      # User networking and friend requests
│   ├── groups/           # Study communities and group chats
│   ├── leaderboard/      # Points, streaks, and rankings
│   ├── main/             # Homepage and core views
│   ├── messages/         # Direct messaging system
│   ├── models/           # SQLAlchemy database models
│   ├── nearby/           # Location-based study discovery
│   ├── notifications/    # User alerts and system notifications
│   ├── points/           # Gamification logic
│   ├── productivity/     # Study tracking and timers
│   ├── questions/        # Q&A forum functionality
│   ├── static/           # CSS, JavaScript, and images
│   └── templates/        # Jinja2 HTML templates
├── migrations/           # Alembic database migration scripts
├── Dockerfile            # Docker configuration for deployment
├── docker-compose.yml    # Local development services (Postgres/Redis)
├── gunicorn_config.py    # WSGI server configuration
├── requirements.txt      # Python dependencies
├── run.py                # Application entry point
└── DEPLOYMENT.md         # Detailed deployment instructions
```

## 💻 Local Development Setup

Follow these steps to run StudyConnect locally on Windows:

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd StudyConnect
   ```

2. **Create a virtual environment:**
   ```powershell
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Install requirements:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   - Copy `.env.example` to a new file named `.env`.
   - Update the placeholder values (see Environment Variables section below).

6. **Configure Database & Redis (Optional but recommended):**
   - You can run PostgreSQL and Redis locally using the provided `docker-compose.yml` file:
     ```powershell
     docker-compose up -d
     ```

7. **Run database migrations:**
   ```powershell
   flask db upgrade
   ```

8. **Start the Flask application:**
   ```powershell
   python run.py
   ```
   The application will be available at `http://localhost:5000`.

## 🔐 Environment Variables

Create a `.env` file in the root directory based on `.env.example`. 

**Important:** Never commit your actual `.env` file or expose database credentials, API keys, or email passwords.

```env
# Flask Configuration
SECRET_KEY=your_secure_random_string
FLASK_APP=run.py
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis (Caching & WebSockets)
REDIS_URL=redis://localhost:6379/0

# Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SUPPRESS_SEND=1 # Set to 1 in dev to print emails to console

# Upload Settings
MAX_CONTENT_LENGTH=5242880
UPLOAD_FOLDER=app/static/uploads
```

## 🗄️ Database

StudyConnect uses **PostgreSQL** for persistent data storage. The production database is securely hosted on **Supabase**. 

Database schema changes are managed using **Flask-Migrate** (Alembic). Always run `flask db upgrade` after pulling new changes to ensure your local schema is up to date.

## ⚡ Redis

**Redis** is utilized in this project for two primary purposes:
1. **Caching:** Fast retrieval of homepage statistics and frequently accessed data to reduce database load (via Flask-Caching).
2. **WebSockets:** Acting as a message broker for Flask-SocketIO to manage real-time communication seamlessly.

## 🚢 Deployment

StudyConnect is currently deployed and running in a production environment.

- **Hosting Platform:** [Railway](https://railway.app/)
- **Infrastructure:** Docker-based deployment using the provided `Dockerfile`.
- **Web Server:** Gunicorn utilizing `GeventWebSocketWorker` to support persistent WebSocket connections alongside standard HTTP requests.
- **Database:** Supabase (PostgreSQL).
- **Caching/Broker:** Railway-provisioned Redis service.

Because the application relies heavily on real-time WebSockets, Railway provides an excellent persistent hosting environment.

🌐 **Live Website:** [https://studyconnect-learn.up.railway.app/](https://studyconnect-learn.up.railway.app/)

## 📌 Current Status

StudyConnect is currently deployed and accessible through the live Railway URL. 

The core application—including authentication, Q&A, communities, messaging, and productivity tracking—is fully operational. 

*Note: Email verification via Gmail SMTP is planned for a future update, as direct SMTP connectivity from the current Railway environment is presently restricted.*

## 🗺️ Roadmap

### Version 1 (Current)
- [x] Core authentication
- [x] Questions & answers
- [x] Communities/groups
- [x] Connections
- [x] Messaging
- [x] Nearby discovery
- [x] Notifications
- [x] Points and leaderboard
- [x] Productivity tracking
- [x] Redis caching
- [x] Railway deployment
- [x] Supabase PostgreSQL

### Version 2 (Planned)
- [ ] Production-ready email verification
- [ ] Improved email delivery using a transactional email provider (e.g., Brevo/SendGrid)
- [ ] Advanced performance optimization
- [ ] Better cache invalidation strategies
- [ ] Additional UI/UX improvements
- [ ] Expanded automated testing and monitoring

## 🛡️ Security

Security best practices implemented in StudyConnect:
- **Environment Secrets:** All sensitive keys and URIs are managed via environment variables.
- **Password Hashing:** Passwords are securely hashed before storage.
- **CSRF Protection:** All forms are protected against Cross-Site Request Forgery using Flask-WTF.
- **Route Protection:** Authentication is enforced on sensitive endpoints using Flask-Login.
- **Data Protection:** Database credentials and the `.env` file are strictly ignored in version control.

## 🤝 Contributing

Contributions are welcome! To contribute:

1. **Fork** the repository.
2. **Create a branch** for your feature or bug fix (`git checkout -b feature/my-new-feature`).
3. **Make changes** and test them locally.
4. **Commit** your changes (`git commit -m 'Add some feature'`).
5. **Push** to the branch (`git push origin feature/my-new-feature`).
6. **Submit a Pull Request** for review.

## 📄 License

Licensing information will be added separately.

## 🔗 Project Links

🌐 **Live Website:** [https://studyconnect-learn.up.railway.app/](https://studyconnect-learn.up.railway.app/)  
💻 **GitHub Repository:** Please refer to the repository URL where this README is hosted.
