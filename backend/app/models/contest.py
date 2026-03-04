"""Contest model."""

from datetime import datetime, timezone
from app.extensions import db


class Contest(db.Model):
    __tablename__ = "contests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    problems = db.relationship("Problem", backref="contest", lazy="dynamic", cascade="all, delete-orphan")
    participants = db.relationship("ContestParticipant", backref="contest", lazy="dynamic", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", backref="contest_ref", overlaps="contest", lazy="dynamic", cascade="all, delete-orphan")
    proctoring_violations = db.relationship("ProctoringViolation", backref="contest_ref", overlaps="contest", lazy="dynamic", cascade="all, delete-orphan")



    @property
    def status(self) -> str:
        """Return current contest status based on time."""
        now = datetime.now(timezone.utc)
        if now < self.start_time:
            return "upcoming"
        elif now > self.end_time:
            return "ended"
        return "active"

    def to_dict(self, include_problems: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_published": self.is_published,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "participant_count": self.participants.count(),
        }
        if include_problems:
            data["problems"] = [p.to_dict() for p in self.problems.all()]
        return data

    def __repr__(self) -> str:
        return f"<Contest {self.title}>"
