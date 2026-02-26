from app import db
from datetime import datetime

class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey("problems.id"), nullable=False)
    contest_id = db.Column(db.Integer, db.ForeignKey("contests.id"), nullable=False)

    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), default="python")

    status = db.Column(db.String(50), default="pending")  
    execution_time = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)