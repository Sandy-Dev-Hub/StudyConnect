from gevent import monkey
monkey.patch_all()

import os
from dotenv import load_dotenv

# Load .env for local development.
# In production (Railway), environment variables are provided
# directly by the hosting platform.
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
