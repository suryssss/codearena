import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-fallback")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Docker Judge settings
    DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "python:3.11-slim")
    DOCKER_TIMEOUT = int(os.getenv("DOCKER_TIMEOUT", 10))
    DOCKER_MEMORY_LIMIT = os.getenv("DOCKER_MEMORY_LIMIT", "128m")
    DOCKER_CPU_LIMIT = int(os.getenv("DOCKER_CPU_LIMIT", 1))

    # Database Connection Pooling
    # These settings prevent "too many connections" crashes under load.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", 20)),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 40)),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", 30)),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 1800)),  # Recycle stale connections every 30 min
        "pool_pre_ping": True,  # Verify connections are alive before using them
    }

    # Rate Limiting
    # RATELIMIT_STORAGE_URI is set dynamically in create_app() after
    # checking Redis connectivity (falls back to memory:// if unavailable).
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200/minute")

    # Scaling
    # How many gunicorn workers to run: (2 * CPU) + 1
    GUNICORN_WORKERS = int(os.getenv("GUNICORN_WORKERS", 4))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Relax rate limits in development
    RATELIMIT_DEFAULT = "1000/minute"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
    }


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
