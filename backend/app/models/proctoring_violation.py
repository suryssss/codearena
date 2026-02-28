"""ProctoringViolation model — tracks proctoring violations per user per contest."""

from datetime import datetime, timezone
from app.extensions import db


class ProctoringViolation(db.Model):
    __tablename__ = "proctoring_violations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    contest_id = db.Column(db.Integer, db.ForeignKey("contests.id"), nullable=False, index=True)
    violation_type = db.Column(db.String(50), nullable=False)
    # violation types: tab_switch, window_blur, copy_paste, right_click, fullscreen_exit
    details = db.Column(db.Text, default="")
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contest_id": self.contest_id,
            "violation_type": self.violation_type,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self) -> str:
        return f"<ProctoringViolation user={self.user_id} type={self.violation_type}>"
