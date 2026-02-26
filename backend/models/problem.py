from app import db

class Problem(db.Model):
    __tablename__ = "problems"

    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey("contests.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    time_limit = db.Column(db.Float, default=1.0)
    memory_limit = db.Column(db.Integer, default=256)

    submissions = db.relationship("Submission", backref="problem", lazy=True)