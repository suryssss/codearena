"""Submission model."""

from datetime import datetime, timezone
from app.extensions import db


class Submission(db.Model):
    __tablename__ = "submissions"

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_ACCEPTED = "accepted"
    STATUS_WRONG_ANSWER = "wrong_answer"
    STATUS_RUNTIME_ERROR = "runtime_error"
    STATUS_TIME_LIMIT = "time_limit_exceeded"
    STATUS_MEMORY_LIMIT = "memory_limit_exceeded"
    STATUS_COMPILATION_ERROR = "compilation_error"

    VALID_STATUSES = [
        STATUS_PENDING, STATUS_RUNNING, STATUS_ACCEPTED,
        STATUS_WRONG_ANSWER, STATUS_RUNTIME_ERROR, STATUS_TIME_LIMIT,
        STATUS_MEMORY_LIMIT, STATUS_COMPILATION_ERROR,
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problems.id"), nullable=False, index=True)
    contest_id = db.Column(db.Integer, db.ForeignKey("contests.id"), nullable=False, index=True)

    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), default="python", nullable=False)

    status = db.Column(db.String(50), default=STATUS_PENDING, nullable=False)
    execution_time = db.Column(db.Float)  # seconds
    memory_used = db.Column(db.Integer)  # KB
    error_message = db.Column(db.Text)
    test_cases_passed = db.Column(db.Integer, default=0)
    total_test_cases = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "problem_id": self.problem_id,
            "contest_id": self.contest_id,
            "language": self.language,
            "status": self.status,
            "execution_time": self.execution_time,
            "memory_used": self.memory_used,
            "error_message": self.error_message,
            "test_cases_passed": self.test_cases_passed,
            "total_test_cases": self.total_test_cases,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Submission {self.id} status={self.status}>"
