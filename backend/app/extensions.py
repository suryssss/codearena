"""
Shared extension instances.

Created here (not in __init__.py) to avoid circular imports.
All extensions are initialized without an app; `init_app` is called
later inside the application factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
import redis

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
socketio = SocketIO()

# Redis client — initialized lazily in create_app
redis_client: redis.Redis = None  # type: ignore
