"""Health and cache monitoring routes."""

from flask import Blueprint, jsonify
import app.extensions as ext

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """System health check — DB + Redis status."""
    status = {"status": "healthy", "services": {}}

    # Check DB
    try:
        from app.extensions import db
        db.session.execute(db.text("SELECT 1"))
        status["services"]["database"] = "connected"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Check Redis
    try:
        if ext.redis_client:
            ext.redis_client.ping()
            status["services"]["redis"] = "connected"
            info = ext.redis_client.info("memory")
            status["services"]["redis_memory"] = info.get("used_memory_human", "unknown")
        else:
            status["services"]["redis"] = "not configured"
    except Exception as e:
        status["services"]["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return jsonify(status), 200 if status["status"] == "healthy" else 503


@health_bp.route("/cache/stats", methods=["GET"])
def cache_stats():
    """Redis cache statistics."""
    client = ext.redis_client
    if not client:
        return jsonify({"error": "Redis not available"}), 503

    try:
        info = client.info()

        # Count cache keys by prefix
        all_cache_keys = client.keys("cache:*")
        leaderboard_keys = client.keys("leaderboard:*")
        judge_queue_len = client.llen("judge_queue")

        key_breakdown = {}
        for key in all_cache_keys:
            prefix = key.split(":")[1] if ":" in key else "other"
            key_breakdown[prefix] = key_breakdown.get(prefix, 0) + 1

        return jsonify({
            "redis_version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "memory": {
                "used": info.get("used_memory_human"),
                "peak": info.get("used_memory_peak_human"),
            },
            "keys": {
                "total": info.get("db0", {}).get("keys", len(all_cache_keys) + len(leaderboard_keys)),
                "cache_keys": len(all_cache_keys),
                "leaderboard_keys": len(leaderboard_keys),
                "judge_queue_length": judge_queue_len,
                "breakdown": key_breakdown,
            },
            "stats": {
                "total_commands": info.get("total_commands_processed"),
                "hits": info.get("keyspace_hits"),
                "misses": info.get("keyspace_misses"),
                "hit_rate": (
                    f"{info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']) * 100:.1f}%"
                    if info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0) > 0
                    else "N/A"
                ),
            },
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
