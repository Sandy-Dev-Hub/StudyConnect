import os
from datetime import timedelta


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').strip() or 'sqlite:///studyconnect.db'

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '1') == '1'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'StudyConnect <noreply@studyconnect.com>')
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', '1') == '1'
    AUTO_VERIFY_USERS = os.environ.get('AUTO_VERIFY_USERS', '0') == '1'

    # Redis / Cache
    REDIS_URL = os.environ.get('REDIS_URL', '')
    if REDIS_URL:
        CACHE_TYPE = 'RedisCache'
        CACHE_REDIS_URL = REDIS_URL
    else:
        CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # Uploads
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join('app', 'static', 'uploads'))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Security
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True

    # Pagination
    QUESTIONS_PER_PAGE = 12
    ANSWERS_PER_PAGE = 20
    LEADERBOARD_PER_PAGE = 25

    # Token expiry (seconds)
    TOKEN_EXPIRY = 3600  # 1 hour

    # Subject and Exam tag choices
    SUBJECT_TAGS = [
        'Mathematics', 'Physics', 'Chemistry', 'Biology',
        'Computer Science', 'English', 'History', 'Geography',
        'Economics', 'Political Science', 'Psychology', 'Sociology',
        'Accountancy', 'Business Studies', 'Other'
    ]

    EXAM_TAGS = [
        'JEE Main', 'JEE Advanced', 'NEET', 'UPSC', 'CAT',
        'GATE', 'GRE', 'SAT', 'CBSE', 'ICSE',
        'State Board', 'University', 'Competitive', 'Other'
    ]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
