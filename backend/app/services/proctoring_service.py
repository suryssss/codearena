"""Proctoring service — business logic for proctoring violation management."""

from app.extensions import db
from app.models.proctoring_violation import ProctoringViolation
from app.models.participant import ContestParticipant
from app.models.user import User


class ProctoringService:

    @staticmethod
    def log_violation(
        user_id: int,
        contest_id: int,
        violation_type: str,
        details: str = "",
        threshold: int = 5,
    ) -> ProctoringViolation:
        """Log a proctoring violation and check if user should be flagged."""
        violation = ProctoringViolation(
            user_id=user_id,
            contest_id=contest_id,
            violation_type=violation_type,
            details=details,
        )
        db.session.add(violation)

        # Update participant violation count
        participant = ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first()
        if participant:
            participant.violation_count = (participant.violation_count or 0) + 1
            # Flag user if threshold exceeded
            if participant.violation_count >= threshold:
                participant.is_flagged = True

        db.session.commit()
        return violation

    @staticmethod
    def get_violation_count(user_id: int, contest_id: int) -> int:
        """Get total violation count for a user in a contest."""
        return ProctoringViolation.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).count()

    @staticmethod
    def is_user_flagged(user_id: int, contest_id: int) -> bool:
        """Check if a user is flagged in a contest."""
        participant = ContestParticipant.query.filter_by(
            user_id=user_id, contest_id=contest_id,
        ).first()
        return participant.is_flagged if participant else False

    @staticmethod
    def get_contest_violations(contest_id: int) -> list[dict]:
        """Get all violations for a contest, grouped by user."""
        violations = ProctoringViolation.query.filter_by(
            contest_id=contest_id,
        ).order_by(ProctoringViolation.timestamp.desc()).all()

        # Group by user
        users_map = {}
        for v in violations:
            uid = v.user_id
            if uid not in users_map:
                user = User.query.get(uid)
                participant = ContestParticipant.query.filter_by(
                    user_id=uid, contest_id=contest_id,
                ).first()
                users_map[uid] = {
                    "user_id": uid,
                    "username": user.username if user else "Unknown",
                    "violation_count": participant.violation_count if participant else 0,
                    "is_flagged": participant.is_flagged if participant else False,
                    "violations": [],
                }
            users_map[uid]["violations"].append(v.to_dict())

        return list(users_map.values())

    @staticmethod
    def get_flagged_users(contest_id: int) -> list[dict]:
        """Get all flagged users for a contest."""
        flagged_participants = ContestParticipant.query.filter_by(
            contest_id=contest_id, is_flagged=True,
        ).all()

        result = []
        for p in flagged_participants:
            user = User.query.get(p.user_id)
            result.append({
                "user_id": p.user_id,
                "username": user.username if user else "Unknown",
                "violation_count": p.violation_count,
                "score": p.score,
                "problems_solved": p.problems_solved,
            })

        return result
