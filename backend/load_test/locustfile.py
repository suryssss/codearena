"""
CodeArena Load Test — Locust Configuration

Simulates realistic user behavior:
  1. Login and get JWT token
  2. Browse contests and problems
  3. Run code against sample test cases (async via queue)
  4. Submit code for full judging

Usage:
  1. First run the setup:   python -m load_test.setup_test_data
  2. Start the server:      python run.py
  3. Run the load test:     locust -f load_test/locustfile.py --host=http://127.0.0.1:5000

  Then open http://localhost:8089 in your browser and configure:
    - Number of users: 1000
    - Spawn rate: 50 (users per second)
    - Host: http://127.0.0.1:5000

Targets:
  - 1000 concurrent users
  - ~200 submissions per minute
  - Mix of read-heavy (browse) and write-heavy (run/submit) operations
"""

import json
import os
import random
import time

from locust import HttpUser, task, between, events

# Load test configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "test_config.json")

try:
    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("ERROR: Run 'python -m load_test.setup_test_data' first!")
    raise

NUM_USERS = CONFIG["num_users"]
PASSWORD = CONFIG["password"]
CONTEST_ID = CONFIG["contest_id"]
PROBLEM_IDS = CONFIG["problem_ids"]

# Code solutions that will pass the test cases
SOLUTIONS = {
    # Sum of Two Numbers
    0: "a, b = map(int, input().split())\nprint(a + b)",
    # Reverse a String
    1: "s = input()\nprint(s[::-1])",
    # FizzBuzz
    2: """n = int(input())
for i in range(1, n + 1):
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
""",
}

# Wrong answers (to create a mix of pass/fail)
WRONG_SOLUTIONS = [
    "print('wrong answer')",
    "import time; time.sleep(5)",  # will TLE
    "raise Exception('boom')",     # will runtime error
    "x = int(input())\nprint(x)",  # wrong logic
]

# Track user index for unique logins
_user_counter = 0


class CodeArenaUser(HttpUser):
    """
    Simulates a CodeArena user during a live contest.

    Behavior mix (weighted):
      - 40% browsing (view contest, view problems) — lightweight reads
      - 25% run code (async via queue) — medium load
      - 15% submit code — heavy load (triggers full judging)
      - 10% check leaderboard — cached reads
      - 10% check submission history — DB reads
    """

    # Wait between 1-5 seconds between actions (realistic user think time)
    wait_time = between(1, 5)

    def on_start(self):
        """Login and store JWT token on user spawn."""
        global _user_counter
        self.user_index = _user_counter % NUM_USERS
        _user_counter += 1

        self.email = f"user_{self.user_index}@loadtest.com"
        self.token = None

        # Login
        with self.client.post(
            "/api/auth/login",
            json={"email": self.email, "password": PASSWORD},
            catch_response=True,
            name="/api/auth/login",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                if self.token:
                    resp.success()
                else:
                    resp.failure("No access_token in response")
            elif resp.status_code == 429:
                resp.failure("Rate limited on login")
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    def _headers(self):
        """Return auth headers."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # BROWSE

    @task(20)
    def view_contest(self):
        """View contest details."""
        self.client.get(
            f"/api/contests/{CONTEST_ID}",
            headers=self._headers(),
            name="/api/contests/[id]",
        )

    @task(20)
    def view_problem(self):
        """View a random problem."""
        problem_id = random.choice(PROBLEM_IDS)
        self.client.get(
            f"/api/problems/{problem_id}",
            headers=self._headers(),
            name="/api/problems/[id]",
        )

    # RUN CODE

    @task(25)
    def run_code(self):
        """Run code against sample test cases (async via Redis queue)."""
        if not self.token:
            return

        problem_idx = random.randint(0, len(PROBLEM_IDS) - 1)
        problem_id = PROBLEM_IDS[problem_idx]

        # 70% correct solutions, 30% wrong
        if random.random() < 0.7:
            code = SOLUTIONS.get(problem_idx, SOLUTIONS[0])
        else:
            code = random.choice(WRONG_SOLUTIONS)

        with self.client.post(
            "/api/submissions/run",
            json={
                "problem_id": problem_id,
                "contest_id": CONTEST_ID,
                "code": code,
                "language": "python",
            },
            headers=self._headers(),
            catch_response=True,
            name="/api/submissions/run",
        ) as resp:
            if resp.status_code in (200, 202):
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limited")
            else:
                resp.failure(f"Run failed: {resp.status_code} {resp.text[:200]}")

    # SUBMIT CODE

    @task(15)
    def submit_code(self):
        """Submit code for full judging (all test cases)."""
        if not self.token:
            return

        problem_idx = random.randint(0, len(PROBLEM_IDS) - 1)
        problem_id = PROBLEM_IDS[problem_idx]

        # 60% correct solutions, 40% wrong
        if random.random() < 0.6:
            code = SOLUTIONS.get(problem_idx, SOLUTIONS[0])
        else:
            code = random.choice(WRONG_SOLUTIONS)

        with self.client.post(
            "/api/submissions",
            json={
                "problem_id": problem_id,
                "contest_id": CONTEST_ID,
                "code": code,
                "language": "python",
            },
            headers=self._headers(),
            catch_response=True,
            name="/api/submissions [SUBMIT]",
        ) as resp:
            if resp.status_code == 201:
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limited")
            else:
                resp.failure(f"Submit failed: {resp.status_code} {resp.text[:200]}")

    # LEADERBOARD

    @task(10)
    def check_leaderboard(self):
        """Check the contest leaderboard (should be cached in Redis)."""
        self.client.get(
            f"/api/leaderboard/{CONTEST_ID}",
            headers=self._headers(),
            name="/api/leaderboard/[id]",
        )

    # SUBMISSION HISTORY

    @task(10)
    def check_my_submissions(self):
        """Check personal submission history."""
        if not self.token:
            return
        self.client.get(
            "/api/submissions/my",
            params={"contest_id": CONTEST_ID},
            headers=self._headers(),
            name="/api/submissions/my",
        )


# Event hooks for logging

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print()
    print("=" * 60)
    print("CodeArena Load Test Starting")
    print(f"  Contest ID: {CONTEST_ID}")
    print(f"  Problems: {PROBLEM_IDS}")
    print(f"  Users pool: {NUM_USERS}")
    print("=" * 60)
    print()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print()
    print("=" * 60)
    print("CodeArena Load Test Complete")
    print("=" * 60)
