"""Leaderboard service — Redis-backed real-time rankings with caching."""

from app.extensions import db
from app.models.participant import ContestParticipant
from app.models.user import User
from app.models.contest import Contest
from app.models.submission import Submission
from app.errors import NotFoundError
from app.utils.cache import (
    cache_get, cache_set, cache_invalidate_leaderboard,
    TTL_SHORT,
)
import app.extensions as ext


class LeaderboardService:

    LEADERBOARD_KEY_PREFIX = "leaderboard:"

    @staticmethod
    def _key(contest_id: int) -> str:
        return f"{LeaderboardService.LEADERBOARD_KEY_PREFIX}{contest_id}"

    @staticmethod
    def update_score(contest_id: int, user_id: int, score: int) -> None:
        """Update a user's score in the Redis sorted set and invalidate cache."""
        redis_client = ext.redis_client
        if redis_client:
            try:
                redis_client.zadd(
                    LeaderboardService._key(contest_id),
                    {str(user_id): score},
                )
            except Exception:
                pass

        # Also update DB for persistence
        participant = ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first()
        if participant:
            participant.score = score
            db.session.commit()

        # Invalidate cached leaderboard JSON
        cache_invalidate_leaderboard(contest_id)

    @staticmethod
    def recalculate_user_score(contest_id: int, user_id: int) -> int:
        """
        Recalculate a user's total score for a contest based on accepted submissions.
        Only counts the best submission per problem.
        """
        from app.models.problem import Problem

        problems = Problem.query.filter_by(contest_id=contest_id).all()
        total_score = 0
        problems_solved = 0

        for problem in problems:
            accepted = Submission.query.filter_by(
                user_id=user_id,
                problem_id=problem.id,
                contest_id=contest_id,
                status=Submission.STATUS_ACCEPTED,
            ).first()
            if accepted:
                total_score += problem.points
                problems_solved += 1

        # Update participant record
        participant = ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first()
        if participant:
            participant.score = total_score
            participant.problems_solved = problems_solved
            db.session.commit()

        # Update Redis sorted set + invalidate cached JSON
        LeaderboardService.update_score(contest_id, user_id, total_score)

        return total_score

    @staticmethod
    def get_leaderboard(contest_id: int) -> list[dict]:
        """
        Get the leaderboard for a contest.
        Uses a 2-layer cache:
        1. Short TTL JSON cache for the full leaderboard response
        2. Redis sorted set for real-time rankings
        Falls back to DB if Redis is unavailable.
        """
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")

        # Layer 1: Check JSON cache first (fastest)
        cache_key = f"cache:leaderboard:{contest_id}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        redis_client = ext.redis_client
        leaderboard = []

        # Layer 2: Try Redis sorted set
        if redis_client:
            try:
                key = LeaderboardService._key(contest_id)
                rankings = redis_client.zrevrange(key, 0, -1, withscores=True)
                if rankings:
                    rank = 1
                    for user_id_str, score in rankings:
                        user = User.query.get(int(user_id_str))
                        if user:
                            participant = ContestParticipant.query.filter_by(
                                user_id=user.id, contest_id=contest_id,
                            ).first()
                            leaderboard.append({
                                "rank": rank,
                                "user_id": user.id,
                                "username": user.username,
                                "score": int(score),
                                "problems_solved": participant.problems_solved if participant else 0,
                            })
                            rank += 1

                    # Cache the result for quick subsequent reads
                    cache_set(cache_key, leaderboard, TTL_SHORT)
                    return leaderboard
            except Exception:
                pass

        # Layer 3: Fallback to DB
        participants = (
            ContestParticipant.query
            .filter_by(contest_id=contest_id)
            .order_by(ContestParticipant.score.desc(), ContestParticipant.total_time.asc())
            .all()
        )

        for rank, participant in enumerate(participants, start=1):
            user = User.query.get(participant.user_id)
            if user:
                leaderboard.append({
                    "rank": rank,
                    "user_id": user.id,
                    "username": user.username,
                    "score": participant.score,
                    "problems_solved": participant.problems_solved,
                })

        # Cache DB result too
        cache_set(cache_key, leaderboard, TTL_SHORT)

        return leaderboard
