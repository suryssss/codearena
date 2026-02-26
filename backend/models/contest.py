from app import db
from datetime import datetime

class Contest(db.Model):
    __tablename__ = "contests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    problems = db.relationship("Problem", backref="contest", lazy=True)