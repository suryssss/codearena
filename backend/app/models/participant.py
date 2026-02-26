"""ContestParticipant model — join table between users and contests."""

from datetime import datetime, timezone
from app.extensions import db


class ContestParticipant(db.Model):
    __tablename__ = "contest_participants"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contest_id = db.Column(db.Integer, db.ForeignKey("contests.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    problems_solved = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)  # total time in seconds
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Unique constraint: user can join a contest only once
    __table_args__ = (
        db.UniqueConstraint("user_id", "contest_id", name="uq_user_contest"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contest_id": self.contest_id,
            "score": self.score,
            "problems_solved": self.problems_solved,
            "total_time": self.total_time,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }

    def __repr__(self) -> str:
        return f"<ContestParticipant user={self.user_id} contest={self.contest_id}>"
