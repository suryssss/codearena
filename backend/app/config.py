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


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
