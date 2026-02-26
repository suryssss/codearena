"""Leaderboard service — Redis-backed real-time rankings."""

from app.extensions import db
from app.models.participant import ContestParticipant
from app.models.user import User
from app.models.contest import Contest
from app.models.submission import Submission
from app.errors import NotFoundError
import app.extensions as ext


class LeaderboardService:

    LEADERBOARD_KEY_PREFIX = "leaderboard:"

    @staticmethod
    def _key(contest_id: int) -> str:
        return f"{LeaderboardService.LEADERBOARD_KEY_PREFIX}{contest_id}"

    @staticmethod
    def update_score(contest_id: int, user_id: int, score: int) -> None:
        """Update a user's score in the Redis sorted set."""
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

        # Update Redis
        LeaderboardService.update_score(contest_id, user_id, total_score)

        return total_score

    @staticmethod
    def get_leaderboard(contest_id: int) -> list[dict]:
        """
        Get the leaderboard for a contest.
        Tries Redis first for speed, falls back to DB.
        """
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")

        redis_client = ext.redis_client
        leaderboard = []

        # Try Redis first
        if redis_client:
            try:
                key = LeaderboardService._key(contest_id)
                # ZREVRANGEBYSCORE returns highest scores first
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
                    return leaderboard
            except Exception:
                pass

        # Fallback to DB
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

        return leaderboard
