from gevent import monkey
monkey.patch_all()

import multiprocessing
import os

# Bind address and port
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")

# Worker configuration for Flask-SocketIO compatibility
_default_workers = (multiprocessing.cpu_count() * 2 + 1) if os.getenv("REDIS_URL") else 1
workers = int(os.getenv("GUNICORN_WORKERS", str(_default_workers)))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker")
worker_connections = 1000
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = 5

# Logging configuration
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s s'

# Process naming
proc_name = "studyconnect_gunicorn"

# Reloading (disabled in production)
reload = os.getenv("FLASK_ENV") == "development"
