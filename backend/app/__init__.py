"""
Application factory for CodeArena backend.
"""

import os
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors, socketio, redis as redis_module
import app.extensions as ext
import redis


def create_app(config_name: str = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'development' or 'production'.
                     Defaults to FLASK_ENV env var or 'development'.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # ── Initialize extensions ────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ── SocketIO ─────────────────────────────────────────────────────
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="eventlet",
        logger=False,
        engineio_logger=False,
    )

    # ── Redis client (optional — app works without it) ─────────────
    try:
        redis_conn = redis.from_url(
            app.config["REDIS_URL"],
            decode_responses=True,
        )
        redis_conn.ping()
        ext.redis_client = redis_conn
        app.logger.info("Redis connected")
    except Exception:
        ext.redis_client = None
        app.logger.warning("Redis not available — judge queue will use synchronous fallback")

    # ── Register blueprints ──────────────────────────────────────────
    _register_blueprints(app)

    # ── Register SocketIO event handlers ─────────────────────────────
    _register_socket_events(app)

    # ── Register error handlers ──────────────────────────────────────
    _register_error_handlers(app)

    # ── Shell context (convenience for `flask shell`) ────────────────
    @app.shell_context_processor
    def make_shell_context():
        return {"db": db, "app": app}

    # ── Start background judge consumer (dev mode) ────────────────
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from app.worker_thread import start_background_judge
        start_background_judge(app)

    return app


def _register_blueprints(app: Flask) -> None:
    """Import and register all route blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.contests import contests_bp
    from app.routes.problems import problems_bp
    from app.routes.submissions import submissions_bp
    from app.routes.leaderboard import leaderboard_bp
    from app.routes.health import health_bp
    from app.routes.proctoring import proctoring_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(contests_bp, url_prefix="/api/contests")
    app.register_blueprint(problems_bp, url_prefix="/api/problems")
    app.register_blueprint(submissions_bp, url_prefix="/api/submissions")
    app.register_blueprint(leaderboard_bp, url_prefix="/api/leaderboard")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(proctoring_bp, url_prefix="/api/proctoring")


def _register_socket_events(app: Flask) -> None:
    """Import and register SocketIO event handlers."""
    from app.sockets import events  # noqa: F401


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""
    from app.errors.handlers import register_error_handlers
    register_error_handlers(app)
