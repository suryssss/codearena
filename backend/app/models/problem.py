"""Problem model."""

from app.extensions import db


class Problem(db.Model):
    __tablename__ = "problems"

    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey("contests.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    input_format = db.Column(db.Text, default="")
    output_format = db.Column(db.Text, default="")
    constraints = db.Column(db.Text, default="")
    sample_input = db.Column(db.Text, default="")
    sample_output = db.Column(db.Text, default="")
    time_limit = db.Column(db.Float, default=2.0)  # seconds
    memory_limit = db.Column(db.Integer, default=256)  # MB
    points = db.Column(db.Integer, default=100)

    # Relationships
    test_cases = db.relationship("TestCase", backref="problem", lazy="dynamic", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", backref="problem_ref", overlaps="problem", lazy="dynamic", cascade="all, delete-orphan")


    def to_dict(self, include_test_cases: bool = False) -> dict:
        data = {
            "id": self.id,
            "contest_id": self.contest_id,
            "title": self.title,
            "description": self.description,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "constraints": self.constraints,
            "sample_input": self.sample_input,
            "sample_output": self.sample_output,
            "time_limit": self.time_limit,
            "memory_limit": self.memory_limit,
            "points": self.points,
        }
        if include_test_cases:
            data["test_cases"] = [tc.to_dict() for tc in self.test_cases.all()]
        return data

    def __repr__(self) -> str:
        return f"<Problem {self.title}>"
