"""
Entry point for the CodeArena backend.
Run with: python run.py
Or:       flask run
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
