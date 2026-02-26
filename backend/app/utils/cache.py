"""
Redis caching utility for CodeArena.

Provides a clean abstraction over Redis for caching with:
- Automatic JSON serialization/deserialization
- Configurable TTL per cache key
- Cache invalidation by key or pattern
- Graceful fallback when Redis is unavailable

Cache key naming convention:
    cache:{resource}:{identifier}
    cache:contests:list
    cache:contest:1
    cache:problems:contest:1
    cache:leaderboard:1
    cache:user:5
"""

import json
import app.extensions as ext

# ── Default TTLs (seconds) ───────────────────────────────────────
TTL_SHORT = 30          # 30 seconds — leaderboard, active contest status
TTL_MEDIUM = 120        # 2 minutes — contest list, problem list
TTL_LONG = 600          # 10 minutes — user profiles, static content
TTL_VERY_LONG = 3600    # 1 hour — rarely changing data


def _get_client():
    """Get Redis client; returns None if unavailable."""
    return ext.redis_client


def cache_get(key: str):
    """
    Retrieve a value from cache.
    Returns deserialized Python object, or None if not found/unavailable.
    """
    client = _get_client()
    if not client:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


def cache_set(key: str, value, ttl: int = TTL_MEDIUM) -> bool:
    """
    Store a value in cache with a TTL.
    Value is JSON-serialized automatically.
    Returns True on success, False on failure.
    """
    client = _get_client()
    if not client:
        return False
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception:
        return False


def cache_delete(key: str) -> bool:
    """Delete a single cache key."""
    client = _get_client()
    if not client:
        return False
    try:
        client.delete(key)
        return True
    except Exception:
        return False


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a glob pattern.
    Example: cache_delete_pattern("cache:contests:*")
    Returns number of keys deleted.
    """
    client = _get_client()
    if not client:
        return 0
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception:
        return 0


def cache_invalidate_contest(contest_id: int = None) -> None:
    """Invalidate all contest-related caches."""
    cache_delete_pattern("cache:contests:*")
    if contest_id:
        cache_delete(f"cache:contest:{contest_id}")
        cache_delete_pattern(f"cache:problems:contest:{contest_id}")


def cache_invalidate_leaderboard(contest_id: int) -> None:
    """Invalidate leaderboard cache for a specific contest."""
    cache_delete(f"cache:leaderboard:{contest_id}")


def cache_invalidate_user(user_id: int) -> None:
    """Invalidate cached user profile."""
    cache_delete(f"cache:user:{user_id}")


# ── Decorator for function-level caching ─────────────────────────

def cached(key_func, ttl: int = TTL_MEDIUM):
    """
    Decorator that caches the return value of a function.

    Usage:
        @cached(lambda contest_id: f"cache:problems:contest:{contest_id}", ttl=120)
        def get_problems(contest_id):
            ...

    The key_func receives the same arguments as the decorated function
    and must return a cache key string.
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            cache_key = key_func(*args, **kwargs)
            result = cache_get(cache_key)
            if result is not None:
                return result
            result = fn(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            return result
        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper
    return decorator
