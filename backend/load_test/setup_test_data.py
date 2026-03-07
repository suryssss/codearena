"""
Setup test data for load testing.

Creates:
- 1 admin user
- 1000 test users (user_0 through user_999)
- 1 active contest
- 3 problems with sample + hidden test cases
- All users joined to the contest

Run: python -m load_test.setup_test_data
"""

import sys
import os
import json
import bcrypt
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.contest import Contest
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.models.participant import ContestParticipant

NUM_USERS = 1000
PASSWORD = "Test1234!"
# Pre-compute hash once (all users share the same test password)
PASSWORD_HASH = bcrypt.hashpw(PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def setup():
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("CodeArena Load Test — Setting Up Test Data")
        print("=" * 60)

        # 1. Create admin user
        admin = User.query.filter_by(email="admin@loadtest.com").first()
        if not admin:
            admin = User(
                username="admin_loadtest",
                email="admin@loadtest.com",
                password_hash=PASSWORD_HASH,
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[+] Admin user created: admin@loadtest.com")
        else:
            print(f"[=] Admin user already exists: admin@loadtest.com")

        # 2. Create 1000 test users
        existing = User.query.filter(User.email.like("user_%@loadtest.com")).count()
        if existing >= NUM_USERS:
            print(f"[=] {existing} test users already exist, skipping")
        else:
            print(f"[*] Creating {NUM_USERS - existing} test users...")
            batch = []
            for i in range(existing, NUM_USERS):
                u = User(
                    username=f"user_{i}",
                    email=f"user_{i}@loadtest.com",
                    password_hash=PASSWORD_HASH,
                )
                batch.append(u)

                if len(batch) >= 100:
                    db.session.add_all(batch)
                    db.session.commit()
                    print(f"    Created users {i - 99} to {i}")
                    batch = []

            if batch:
                db.session.add_all(batch)
                db.session.commit()
                print(f"    Created remaining {len(batch)} users")
            print(f"[+] {NUM_USERS} test users ready")

        # 3. Create contest
        contest = Contest.query.filter_by(title="Load Test Contest").first()
        if not contest:
            contest = Contest(
                title="Load Test Contest",
                description="Stress test contest for 1000 concurrent users",
                start_time=datetime.now(timezone.utc) - timedelta(hours=1),
                end_time=datetime.now(timezone.utc) + timedelta(hours=24),
                is_published=True,
                created_by=admin.id,
            )
            db.session.add(contest)
            db.session.commit()
            print(f"[+] Contest created: '{contest.title}' (id={contest.id}, status={contest.status})")
        else:
            # Make sure it's still active by extending end_time
            contest.end_time = datetime.now(timezone.utc) + timedelta(hours=24)
            db.session.commit()
            print(f"[=] Contest exists: '{contest.title}' (id={contest.id}, status={contest.status})")

        # 4. Create problems
        problems_data = [
            {
                "title": "Sum of Two Numbers",
                "description": "Given two integers A and B, print their sum.",
                "input_format": "Two space-separated integers A and B",
                "output_format": "A single integer — the sum of A and B",
                "constraints": "1 ≤ A, B ≤ 10^9",
                "sample_input": "3 5",
                "sample_output": "8",
                "points": 100,
                "time_limit": 2.0,
                "memory_limit": 256,
                "test_cases": [
                    ("3 5", "8", True),
                    ("0 0", "0", True),
                    ("100 200", "300", False),
                    ("999999999 1", "1000000000", False),
                    ("-5 10", "5", False),
                ],
            },
            {
                "title": "Reverse a String",
                "description": "Given a string S, print it reversed.",
                "input_format": "A single string S",
                "output_format": "The reversed string",
                "constraints": "1 ≤ len(S) ≤ 10^5",
                "sample_input": "hello",
                "sample_output": "olleh",
                "points": 150,
                "time_limit": 2.0,
                "memory_limit": 256,
                "test_cases": [
                    ("hello", "olleh", True),
                    ("a", "a", True),
                    ("abcdef", "fedcba", False),
                    ("racecar", "racecar", False),
                ],
            },
            {
                "title": "FizzBuzz",
                "description": "Given N, print numbers 1 to N. For multiples of 3 print 'Fizz', for multiples of 5 print 'Buzz', for both print 'FizzBuzz'.",
                "input_format": "A single integer N",
                "output_format": "N lines of output",
                "constraints": "1 ≤ N ≤ 100",
                "sample_input": "5",
                "sample_output": "1\n2\nFizz\n4\nBuzz",
                "points": 200,
                "time_limit": 2.0,
                "memory_limit": 256,
                "test_cases": [
                    ("5", "1\n2\nFizz\n4\nBuzz", True),
                    ("1", "1", True),
                    ("15", "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz", False),
                ],
            },
        ]

        problem_ids = []
        for pdata in problems_data:
            p = Problem.query.filter_by(
                title=pdata["title"], contest_id=contest.id
            ).first()
            if not p:
                p = Problem(
                    title=pdata["title"],
                    description=pdata["description"],
                    input_format=pdata["input_format"],
                    output_format=pdata["output_format"],
                    constraints=pdata["constraints"],
                    sample_input=pdata["sample_input"],
                    sample_output=pdata["sample_output"],
                    points=pdata["points"],
                    time_limit=pdata["time_limit"],
                    memory_limit=pdata["memory_limit"],
                    contest_id=contest.id,
                )
                db.session.add(p)
                db.session.commit()

                for order, (inp, out, is_sample) in enumerate(pdata["test_cases"]):
                    tc = TestCase(
                        problem_id=p.id,
                        input_data=inp,
                        expected_output=out,
                        is_sample=is_sample,
                        order=order,
                    )
                    db.session.add(tc)
                db.session.commit()
                print(f"[+] Problem '{p.title}' (id={p.id}) with {len(pdata['test_cases'])} test cases")
            else:
                print(f"[=] Problem '{p.title}' (id={p.id}) already exists")
            problem_ids.append(p.id)

        # 5. Join all users to the contest
        existing_participants = ContestParticipant.query.filter_by(
            contest_id=contest.id
        ).count()

        if existing_participants >= NUM_USERS:
            print(f"[=] {existing_participants} users already joined contest")
        else:
            all_users = User.query.filter(
                User.email.like("%@loadtest.com")
            ).all()

            joined = set(
                p.user_id for p in ContestParticipant.query.filter_by(
                    contest_id=contest.id
                ).all()
            )

            batch = []
            for user in all_users:
                if user.id not in joined:
                    batch.append(ContestParticipant(
                        user_id=user.id,
                        contest_id=contest.id,
                    ))
                    if len(batch) >= 200:
                        db.session.add_all(batch)
                        db.session.commit()
                        batch = []

            if batch:
                db.session.add_all(batch)
                db.session.commit()

            total = ContestParticipant.query.filter_by(contest_id=contest.id).count()
            print(f"[+] {total} users joined the contest")

        # 6. Save config for locust
        config = {
            "num_users": NUM_USERS,
            "password": PASSWORD,
            "contest_id": contest.id,
            "problem_ids": problem_ids,
        }
        config_path = os.path.join(os.path.dirname(__file__), "test_config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print()
        print("=" * 60)
        print("✓ Setup complete!")
        print(f"  Contest ID: {contest.id}")
        print(f"  Problems: {problem_ids}")
        print(f"  Users: user_0@loadtest.com ... user_{NUM_USERS-1}@loadtest.com")
        print(f"  Password: {PASSWORD}")
        print(f"  Config saved to: {config_path}")
        print()
        print("Next: Run the load test with:")
        print("  locust -f load_test/locustfile.py --host=http://127.0.0.1:5000")
        print("=" * 60)


if __name__ == "__main__":
    setup()
