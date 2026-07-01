import eventlet
eventlet.monkey_patch()

import os
import time
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

from flask import Flask, g, request
import markdown2

from app.config import config_by_name

# Setup slow query logging hook
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    times = conn.info.get("query_start_time", [])
    if times:
        start_time = times.pop(-1)
        duration = (time.time() - start_time) * 1000
        if duration > 100:
            logging.warning(f"[SLOW QUERY >100ms] ({duration:.2f}ms): {statement[:200]}...")


def create_app(config_name=None):
    """Application factory for StudyConnect."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))

    # Initialize extensions
    _init_extensions(app)

    # Register middleware
    _register_middleware(app)

    # Register blueprints
    _register_blueprints(app)

    # Register context processors
    _register_context_processors(app)

    # Register template filters
    _register_template_filters(app)

    # Ensure upload directory exists
    upload_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    # Setup logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    return app


def _register_middleware(app):
    """Register HTTP request timing, security headers, and asset caching middleware."""
    @app.before_request
    def before_request_timing():
        g.start_time = time.time()

    @app.after_request
    def after_request_timing_and_headers(response):
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            if request.path.startswith('/api/'):
                app.logger.info(f"[API LATENCY] {request.method} {request.path} -> {response.status_code} ({duration:.2f}ms)")
            elif duration > 500:
                app.logger.warning(f"[SLOW REQUEST >500ms] {request.method} {request.path} -> {response.status_code} ({duration:.2f}ms)")

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Static asset optimization (caching headers)
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'

        return response


def _init_extensions(app):
    """Initialize Flask extensions."""
    from app.extensions import db, migrate, login_manager, mail, csrf, cache, socketio

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    socketio_kwargs = {
        'cors_allowed_origins': '*',
        'async_mode': 'eventlet',
        'ping_timeout': 60,
        'ping_interval': 25
    }
    if app.config.get('REDIS_URL'):
        socketio_kwargs['message_queue'] = app.config.get('REDIS_URL')
    socketio.init_app(app, **socketio_kwargs)

    with app.app_context():
        from app.models import User, Question, Answer, Vote, PointsLog, StudyStreak, StudyGroup, GroupMember, UserProfile, Connection, Conversation, Message, StudyRequest, StudySession, PomodoroRoom, StudyGoal  # noqa: F401



def _register_blueprints(app):
    """Register all application blueprints."""
    from app.main import main_bp
    from app.auth import auth_bp
    from app.questions import questions_bp
    from app.answers import answers_bp
    from app.points import points_bp
    from app.leaderboard import leaderboard_bp
    from app.api import api_bp
    from app.groups import groups_bp
    from app.connections import connections_bp
    from app.messages import messages_bp
    from app.nearby import nearby_bp
    from app.productivity import productivity_bp
    from app.notifications import notifications_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(answers_bp)
    app.register_blueprint(points_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(connections_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(nearby_bp)
    app.register_blueprint(productivity_bp)
    app.register_blueprint(notifications_bp)


def _register_context_processors(app):
    """Register template context processors."""
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.models.connection import Connection
        from app.messages.services import get_unread_message_count
        from app.notifications.services import get_unread_notification_count
        context = {
            'app_name': 'StudyConnect',
            'subject_tags': app.config.get('SUBJECT_TAGS', []),
            'exam_tags': app.config.get('EXAM_TAGS', []),
        }
        if current_user.is_authenticated:
            context['user_points'] = current_user.total_points
            context['user_streak'] = current_user.current_streak
            context['pending_connections_count'] = Connection.query.filter_by(recipient_id=current_user.id, status='pending').count()
            context['unread_messages_count'] = get_unread_message_count(current_user.id)
            context['unread_notifications_count'] = get_unread_notification_count(current_user.id)
        return context


def _register_template_filters(app):
    """Register custom Jinja2 template filters."""
    @app.template_filter('markdown')
    def markdown_filter(text):
        """Convert markdown text to HTML."""
        if not text:
            return ''
        return markdown2.markdown(
            text,
            extras=[
                'fenced-code-blocks',
                'code-friendly',
                'tables',
                'strike',
                'task_list',
                'cuddled-lists',
                'header-ids',
            ],
            safe_mode='escape'
        )

    @app.template_filter('pluralize')
    def pluralize_filter(count, singular='', plural='s'):
        """Simple pluralization filter."""
        return singular if count == 1 else plural
