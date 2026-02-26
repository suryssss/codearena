"""TestCase model — stores hidden test cases for problems."""

from app.extensions import db


class TestCase(db.Model):
    __tablename__ = "test_cases"

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("problems.id"), nullable=False, index=True)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_sample = db.Column(db.Boolean, default=False)  # True = visible to users
    order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "problem_id": self.problem_id,
            "input_data": self.input_data,
            "expected_output": self.expected_output,
            "is_sample": self.is_sample,
            "order": self.order,
        }

    def __repr__(self) -> str:
        return f"<TestCase problem={self.problem_id} order={self.order}>"
