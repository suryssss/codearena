"""
Entry point for the CodeArena backend.
Run with: python run.py
Or:       flask run
"""

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000, use_reloader=True)
