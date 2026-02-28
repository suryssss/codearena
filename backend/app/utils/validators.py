"""Input validation schemas using Marshmallow."""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError


# ── Auth Schemas ──────────────────────────────────────────────────────────────

class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


# ── Contest Schemas ───────────────────────────────────────────────────────────

class ContestCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(load_default="")
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    is_published = fields.Bool(load_default=False)

    @validates_schema
    def validate_times(self, data, **kwargs):
        if data["start_time"] >= data["end_time"]:
            raise ValidationError("end_time must be after start_time")


class ContestUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str()
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    is_published = fields.Bool()


# ── Problem Schemas ───────────────────────────────────────────────────────────

class TestCaseSchema(Schema):
    input_data = fields.Str(required=True)
    expected_output = fields.Str(required=True)
    is_sample = fields.Bool(load_default=False)
    order = fields.Int(load_default=0)


class ProblemCreateSchema(Schema):
    contest_id = fields.Int(required=True)
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(required=True)
    input_format = fields.Str(load_default="")
    output_format = fields.Str(load_default="")
    constraints = fields.Str(load_default="")
    sample_input = fields.Str(load_default="")
    sample_output = fields.Str(load_default="")
    time_limit = fields.Float(load_default=2.0, validate=validate.Range(min=0.5, max=30))
    memory_limit = fields.Int(load_default=256, validate=validate.Range(min=16, max=1024))
    points = fields.Int(load_default=100, validate=validate.Range(min=1))
    test_cases = fields.List(fields.Nested(TestCaseSchema), load_default=[])


class ProblemUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str()
    input_format = fields.Str()
    output_format = fields.Str()
    constraints = fields.Str()
    sample_input = fields.Str()
    sample_output = fields.Str()
    time_limit = fields.Float(validate=validate.Range(min=0.5, max=30))
    memory_limit = fields.Int(validate=validate.Range(min=16, max=1024))
    points = fields.Int(validate=validate.Range(min=1))


# ── Submission Schemas ────────────────────────────────────────────────────────

class SubmissionCreateSchema(Schema):
    problem_id = fields.Int(required=True)
    contest_id = fields.Int(required=True)
    code = fields.Str(required=True, validate=validate.Length(min=1, max=50000))
    language = fields.Str(load_default="python", validate=validate.OneOf(["python"]))


class RunCodeSchema(Schema):
    """Schema for RUN mode — runs sample test cases only."""
    problem_id = fields.Int(required=True)
    contest_id = fields.Int(required=True)
    code = fields.Str(required=True, validate=validate.Length(min=1, max=50000))
    language = fields.Str(load_default="python", validate=validate.OneOf(["python"]))
