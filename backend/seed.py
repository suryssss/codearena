"""
Seed script — creates initial admin user and sample contest data.
Usage: python seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.contest import Contest
from app.models.problem import Problem
from app.models.test_case import TestCase


def seed():
    app = create_app()

    with app.app_context():
        print("[Seed] Creating tables...")
        db.create_all()

        # Create admin user
        admin = User.query.filter_by(email="admin@codearena.dev").first()
        if not admin:
            admin = AuthService.register(
                username="admin",
                email="admin@codearena.dev",
                password="admin123",
            )
            admin.is_admin = True
            db.session.commit()
            print("[Seed] Admin user created: admin@codearena.dev / admin123")
        else:
            print("[Seed] Admin user already exists")

        # Create test user
        test_user = User.query.filter_by(email="user@test.dev").first()
        if not test_user:
            AuthService.register(
                username="testuser",
                email="user@test.dev",
                password="test123",
            )
            print("[Seed] Test user created: user@test.dev / test123")
        else:
            print("[Seed] Test user already exists")

        # Create sample contest
        contest = Contest.query.filter_by(title="Sample Contest").first()
        if not contest:
            now = datetime.now(timezone.utc)
            contest = Contest(
                title="Sample Contest",
                description="A sample coding contest to test the platform. Solve problems, earn points, climb the leaderboard!",
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=23),
                is_published=True,
                created_by=admin.id,
            )
            db.session.add(contest)
            db.session.flush()

            # Problem 1: Two Sum
            p1 = Problem(
                contest_id=contest.id,
                title="Two Sum",
                description="Given two integers a and b, print their sum.",
                input_format="Two space-separated integers a and b (-10^9 <= a, b <= 10^9)",
                output_format="A single integer — the sum of a and b.",
                constraints="Time limit: 1 second\nMemory limit: 256 MB",
                sample_input="3 5",
                sample_output="8",
                time_limit=2.0,
                memory_limit=256,
                points=100,
            )
            db.session.add(p1)
            db.session.flush()

            # Test cases for Two Sum
            test_cases_p1 = [
                ("3 5", "8", True),
                ("0 0", "0", False),
                ("-1 1", "0", False),
                ("1000000000 1000000000", "2000000000", False),
                ("-999999999 999999999", "0", False),
            ]
            for inp, out, is_sample in test_cases_p1:
                db.session.add(TestCase(
                    problem_id=p1.id,
                    input_data=inp,
                    expected_output=out,
                    is_sample=is_sample,
                    order=test_cases_p1.index((inp, out, is_sample)),
                ))

            # Problem 2: FizzBuzz
            p2 = Problem(
                contest_id=contest.id,
                title="FizzBuzz",
                description="Given an integer n, print numbers from 1 to n. For multiples of 3, print 'Fizz'. For multiples of 5, print 'Buzz'. For multiples of both, print 'FizzBuzz'.",
                input_format="A single integer n (1 <= n <= 100)",
                output_format="Print n lines — each line contains either the number, 'Fizz', 'Buzz', or 'FizzBuzz'.",
                constraints="Time limit: 1 second\nMemory limit: 256 MB",
                sample_input="5",
                sample_output="1\n2\nFizz\n4\nBuzz",
                time_limit=2.0,
                memory_limit=256,
                points=150,
            )
            db.session.add(p2)
            db.session.flush()

            # Test cases for FizzBuzz
            db.session.add(TestCase(
                problem_id=p2.id,
                input_data="5",
                expected_output="1\n2\nFizz\n4\nBuzz",
                is_sample=True,
                order=0,
            ))
            db.session.add(TestCase(
                problem_id=p2.id,
                input_data="15",
                expected_output="1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz",
                is_sample=False,
                order=1,
            ))
            db.session.add(TestCase(
                problem_id=p2.id,
                input_data="1",
                expected_output="1",
                is_sample=False,
                order=2,
            ))

            # Problem 3: Reverse String
            p3 = Problem(
                contest_id=contest.id,
                title="Reverse String",
                description="Given a string s, print the reversed string.",
                input_format="A single string s (1 <= len(s) <= 1000)",
                output_format="The reversed string.",
                constraints="Time limit: 1 second\nMemory limit: 256 MB",
                sample_input="hello",
                sample_output="olleh",
                time_limit=2.0,
                memory_limit=256,
                points=100,
            )
            db.session.add(p3)
            db.session.flush()

            db.session.add(TestCase(
                problem_id=p3.id,
                input_data="hello",
                expected_output="olleh",
                is_sample=True,
                order=0,
            ))
            db.session.add(TestCase(
                problem_id=p3.id,
                input_data="abcdef",
                expected_output="fedcba",
                is_sample=False,
                order=1,
            ))
            db.session.add(TestCase(
                problem_id=p3.id,
                input_data="a",
                expected_output="a",
                is_sample=False,
                order=2,
            ))

            db.session.commit()
            print(f"[Seed] Sample contest created with {3} problems")
        else:
            print("[Seed] Sample contest already exists")

        print("[Seed] Done!")


if __name__ == "__main__":
    seed()
