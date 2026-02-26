"""Contest service — business logic for contest management."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.contest import Contest
from app.models.participant import ContestParticipant
from app.errors import NotFoundError, ConflictError, ForbiddenError, APIError


class ContestService:

    @staticmethod
    def create_contest(data: dict, admin_id: int) -> Contest:
        """Create a new contest (admin only)."""
        contest = Contest(
            title=data["title"],
            description=data.get("description", ""),
            start_time=data["start_time"],
            end_time=data["end_time"],
            is_published=data.get("is_published", False),
            created_by=admin_id,
        )
        db.session.add(contest)
        db.session.commit()
        return contest

    @staticmethod
    def update_contest(contest_id: int, data: dict) -> Contest:
        """Update a contest (admin only)."""
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")

        for key, value in data.items():
            if hasattr(contest, key):
                setattr(contest, key, value)
        db.session.commit()
        return contest

    @staticmethod
    def delete_contest(contest_id: int) -> None:
        """Delete a contest (admin only)."""
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")
        db.session.delete(contest)
        db.session.commit()

    @staticmethod
    def get_contest(contest_id: int) -> Contest:
        """Get a single contest by ID."""
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")
        return contest

    @staticmethod
    def list_contests(published_only: bool = True) -> list[Contest]:
        """List all contests. Non-admins only see published contests."""
        query = Contest.query
        if published_only:
            query = query.filter_by(is_published=True)
        return query.order_by(Contest.start_time.desc()).all()

    @staticmethod
    def join_contest(contest_id: int, user_id: int) -> ContestParticipant:
        """Join a contest as a participant."""
        contest = Contest.query.get(contest_id)
        if not contest:
            raise NotFoundError("Contest not found")

        if contest.status == "ended":
            raise APIError("Contest has already ended", status_code=400)

        existing = ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first()
        if existing:
            raise ConflictError("Already joined this contest")

        participant = ContestParticipant(
            user_id=user_id,
            contest_id=contest_id,
        )
        db.session.add(participant)
        db.session.commit()
        return participant

    @staticmethod
    def is_participant(contest_id: int, user_id: int) -> bool:
        """Check if a user has joined a contest."""
        return ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first() is not None
