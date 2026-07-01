import eventlet
eventlet.monkey_patch()

import os
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Copy .env.example to .env for first-time setup
    example_path = os.path.join(basedir, '.env.example')
    if os.path.exists(example_path):
        import shutil
        shutil.copy(example_path, env_path)
        load_dotenv(env_path)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
