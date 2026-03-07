"""
Shared extension instances.

Created here (not in __init__.py) to avoid circular imports.
All extensions are initialized without an app; `init_app` is called
later inside the application factory.
"""

import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

# SocketIO with Redis message queue for multi-instance sync
# The message_queue is set during init_app in create_app().
# This allows SocketIO events emitted from ANY server instance
# (or from the standalone judge worker) to reach ALL connected clients.
socketio = SocketIO()

# Rate Limiter
# Uses Redis as backend storage so rate limits are shared across
# all API instances behind a load balancer.
limiter = Limiter(
    key_func=get_remote_address,
)

# Redis client — initialized lazily in create_app
redis_client: redis.Redis = None  # type: ignore
