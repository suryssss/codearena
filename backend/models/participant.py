from app import db

class ContestParticipant(db.Model):
    __tablename__ = "contest_participants"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contest_id = db.Column(db.Integer, db.ForeignKey("contests.id"), nullable=False)

    score = db.Column(db.Integer, default=0)