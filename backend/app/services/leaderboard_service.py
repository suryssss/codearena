"""Leaderboard service — Redis-backed real-time rankings with penalty scoring and SocketIO."""

from datetime import datetime, timezone

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

    LEADERBOARD_KEY_PREFIX = "contest:"

    @staticmethod
    def _key(contest_id: int) -> str:
        return f"{LeaderboardService.LEADERBOARD_KEY_PREFIX}{contest_id}:leaderboard"

    @staticmethod
    def _calculate_score(solved_count: int, penalty_time: int) -> int:
        """
        Score formula: score = solved_count * 1000 - total_penalty_time
        Higher is better.
        """
        return solved_count * 1000 - penalty_time

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
        Uses formula: score = solved_count * 1000 - penalty_time
        Only counts the first accepted submission per problem.
        """
        from app.models.problem import Problem

        contest = Contest.query.get(contest_id)
        problems = Problem.query.filter_by(contest_id=contest_id).all()
        total_score = 0
        problems_solved = 0
        total_penalty = 0

        for problem in problems:
            # Get first accepted submission for this problem
            accepted = Submission.query.filter_by(
                user_id=user_id,
                problem_id=problem.id,
                contest_id=contest_id,
                status=Submission.STATUS_ACCEPTED,
            ).order_by(Submission.created_at.asc()).first()

            if accepted:
                problems_solved += 1

                # Calculate penalty: time from contest start to accepted submission
                if contest and contest.start_time and accepted.created_at:
                    start = contest.start_time
                    submit_time = accepted.created_at
                    # Ensure both are timezone-aware or both naive
                    if start.tzinfo and not submit_time.tzinfo:
                        submit_time = submit_time.replace(tzinfo=timezone.utc)
                    elif not start.tzinfo and submit_time.tzinfo:
                        start = start.replace(tzinfo=timezone.utc)

                    penalty_seconds = max(0, int((submit_time - start).total_seconds()))

                    # Count wrong attempts before first AC (each adds 20 min penalty)
                    wrong_attempts = Submission.query.filter(
                        Submission.user_id == user_id,
                        Submission.problem_id == problem.id,
                        Submission.contest_id == contest_id,
                        Submission.status != Submission.STATUS_ACCEPTED,
                        Submission.status != Submission.STATUS_PENDING,
                        Submission.status != Submission.STATUS_RUNNING,
                        Submission.created_at < accepted.created_at,
                    ).count()

                    total_penalty += penalty_seconds + (wrong_attempts * 20 * 60)  # 20 min each

        # Calculate final score
        total_score = LeaderboardService._calculate_score(problems_solved, total_penalty)

        # Get old rank before updating
        old_rank = LeaderboardService._get_user_rank(contest_id, user_id)

        # Update participant record
        participant = ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first()
        if participant:
            participant.score = total_score
            participant.problems_solved = problems_solved
            participant.penalty_time = total_penalty
            db.session.commit()

        # Update Redis sorted set + invalidate cached JSON
        LeaderboardService.update_score(contest_id, user_id, total_score)

        # Get new rank and emit events
        new_rank = LeaderboardService._get_user_rank(contest_id, user_id)
        LeaderboardService._emit_updates(contest_id, user_id, old_rank, new_rank)

        return total_score

    @staticmethod
    def _get_user_rank(contest_id: int, user_id: int) -> int:
        """Get user's current rank from Redis or DB."""
        redis_client = ext.redis_client
        if redis_client:
            try:
                rank = redis_client.zrevrank(
                    LeaderboardService._key(contest_id),
                    str(user_id),
                )
                if rank is not None:
                    return rank + 1  # 0-indexed -> 1-indexed
            except Exception:
                pass

        # Fallback: DB-based rank
        participants = (
            ContestParticipant.query
            .filter_by(contest_id=contest_id)
            .order_by(ContestParticipant.score.desc(), ContestParticipant.penalty_time.asc())
            .all()
        )
        for i, p in enumerate(participants, 1):
            if p.user_id == user_id:
                return i
        return 0

    @staticmethod
    def _emit_updates(contest_id: int, user_id: int, old_rank: int, new_rank: int):
        """Emit real-time SocketIO events for leaderboard and rank changes."""
        try:
            from app.sockets.events import emit_leaderboard_update, emit_rank_change

            # Emit updated leaderboard
            leaderboard = LeaderboardService.get_leaderboard(contest_id)
            emit_leaderboard_update(contest_id, leaderboard)

            # Emit rank change if applicable
            if old_rank != new_rank and new_rank > 0:
                user = User.query.get(user_id)
                emit_rank_change(
                    contest_id, user_id,
                    old_rank, new_rank,
                    user.username if user else "Unknown",
                )
        except Exception as e:
            print(f"[Leaderboard] SocketIO emit error (non-fatal): {e}")

    @staticmethod
    def get_performance_percentile(contest_id: int, user_id: int) -> float:
        """Calculate 'Faster than X% of participants' for a user."""
        participants = ContestParticipant.query.filter_by(contest_id=contest_id).all()
        if not participants:
            return 0.0

        user_participant = None
        for p in participants:
            if p.user_id == user_id:
                user_participant = p
                break

        if not user_participant:
            return 0.0

        # Count how many participants have a lower score (worse)
        worse_count = sum(1 for p in participants if p.score < user_participant.score)
        total = len(participants)

        return round((worse_count / total) * 100, 1) if total > 0 else 0.0

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
                                "penalty_time": participant.penalty_time if participant else 0,
                                "is_flagged": participant.is_flagged if participant else False,
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
            .order_by(ContestParticipant.score.desc(), ContestParticipant.penalty_time.asc())
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
                    "penalty_time": participant.penalty_time or 0,
                    "is_flagged": participant.is_flagged or False,
                })

        # Cache DB result too
        cache_set(cache_key, leaderboard, TTL_SHORT)

        return leaderboard
