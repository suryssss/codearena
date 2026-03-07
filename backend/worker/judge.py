"""
Judge worker — pulls submissions from Redis queues and evaluates them.

This runs as a separate process from the Flask app.
Usage: python -m worker.judge

Handles TWO queues:
  1. judge_queue — SUBMIT mode (full test case judging, saved to DB)
  2. run_queue   — RUN mode (sample test cases only, result cached in Redis)

Both queues can be consumed by multiple worker instances for horizontal scale.
Just spin up more workers:  python -m worker.judge
They'll all safely compete for items on the same Redis queues.
"""

import sys
import os
import json
import time

# Add project root to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.submission import Submission
from app.models.test_case import TestCase
from app.services.leaderboard_service import LeaderboardService
from worker.executor import CodeExecutor
import app.extensions as ext


def judge_submission(submission_id: int, executor: CodeExecutor) -> None:
    """
    Judge a single submission against all test cases.

    Flow:
    1. Load submission and its test cases
    2. Mark as 'running'
    3. Execute code against each test case
    4. Compare output
    5. Update status and score
    6. Emit real-time events via SocketIO
    """
    submission = Submission.query.get(submission_id)
    if not submission:
        print(f"[Judge] Submission {submission_id} not found, skipping")
        return

    # Mark as running
    submission.status = Submission.STATUS_RUNNING
    db.session.commit()

    # Emit running status via SocketIO
    _emit_submission_status(submission)

    # Get test cases
    test_cases = TestCase.query.filter_by(
        problem_id=submission.problem_id,
    ).order_by(TestCase.order).all()

    if not test_cases:
        submission.status = Submission.STATUS_ACCEPTED
        submission.test_cases_passed = 0
        submission.total_test_cases = 0
        db.session.commit()
        _emit_submission_status(submission)
        print(f"[Judge] Submission {submission_id}: No test cases, marking accepted")
        return

    submission.total_test_cases = len(test_cases)
    passed = 0
    max_time = 0.0
    final_status = Submission.STATUS_ACCEPTED

    from app.models.problem import Problem
    problem = Problem.query.get(submission.problem_id)
    time_limit = problem.time_limit if problem else 5.0

    for i, tc in enumerate(test_cases):
        print(f"[Judge] Submission {submission_id}: Running test case {i + 1}/{len(test_cases)}")

        result = executor.execute(
            code=submission.code,
            input_data=tc.input_data,
            timeout=time_limit,
        )

        max_time = max(max_time, result["execution_time"])

        # Check for TLE
        if result["timed_out"]:
            final_status = Submission.STATUS_TIME_LIMIT
            #error message in SUBMIT mode
            submission.error_message = "Time limit exceeded"
            break

        # Check for runtime error
        if result["exit_code"] != 0:
            final_status = Submission.STATUS_RUNTIME_ERROR
            #stack trace in SUBMIT mode
            submission.error_message = "Runtime error"
            break

        # Compare output
        actual = result["stdout"].strip()
        expected = tc.expected_output.strip()

        if actual == expected:
            passed += 1
        else:
            final_status = Submission.STATUS_WRONG_ANSWER
            submission.error_message = f"Wrong answer on test case {i + 1}"
            break

    # Update submission
    submission.status = final_status
    submission.test_cases_passed = passed
    submission.execution_time = round(max_time, 4)
    db.session.commit()

    print(f"[Judge] Submission {submission_id}: {final_status} ({passed}/{len(test_cases)} passed, {max_time:.3f}s)")

    # Emit final result via SocketIO
    _emit_submission_status(submission)

    # Update leaderboard if accepted
    if final_status == Submission.STATUS_ACCEPTED:
        LeaderboardService.recalculate_user_score(
            contest_id=submission.contest_id,
            user_id=submission.user_id,
        )


def _emit_submission_status(submission: Submission) -> None:
    """Emit submission status update via SocketIO."""
    try:
        from app.sockets.events import emit_submission_result
        emit_submission_result(
            contest_id=submission.contest_id,
            submission_data={
                "id": submission.id,
                "user_id": submission.user_id,
                "problem_id": submission.problem_id,
                "contest_id": submission.contest_id,
                "status": submission.status,
                "test_cases_passed": submission.test_cases_passed,
                "total_test_cases": submission.total_test_cases,
                "execution_time": submission.execution_time,
                # No error_message or code in SUBMIT mode events
            },
        )
    except Exception as e:
        print(f"[Judge] SocketIO emit error (non-fatal): {e}")


# RUN Queue Processing

def process_run_job(job_payload: dict, executor: CodeExecutor) -> None:
    """
    Process a RUN mode job — execute code against sample test cases.

    Results are:
    1. Emitted via SocketIO 'run_result' to the user's personal room
    2. Cached in Redis for 5 minutes as a polling fallback
    """
    job_id = job_payload["job_id"]
    user_id = job_payload["user_id"]
    code = job_payload["code"]
    time_limit = job_payload.get("time_limit", 5.0)
    test_cases = job_payload["test_cases"]

    print(f"[Run Worker] Processing job {job_id} for user {user_id}")

    results = []
    overall_status = "passed"

    for i, tc_data in enumerate(test_cases):
        exec_result = executor.execute(
            code=code,
            input_data=tc_data["input_data"],
            timeout=time_limit,
        )

        actual = exec_result["stdout"].strip()
        expected = tc_data["expected_output"].strip()

        if exec_result["timed_out"]:
            tc_status = "time_limit_exceeded"
            overall_status = "time_limit_exceeded"
        elif exec_result["exit_code"] != 0:
            tc_status = "runtime_error"
            overall_status = "runtime_error"
        elif actual == expected:
            tc_status = "passed"
        else:
            tc_status = "wrong_answer"
            overall_status = "wrong_answer"

        results.append({
            "test_case": i + 1,
            "status": tc_status,
            "input": tc_data["input_data"],
            "expected_output": expected,
            "actual_output": actual,
            "stdout": exec_result["stdout"],
            "stderr": exec_result["stderr"],
            "execution_time": round(exec_result["execution_time"], 4),
        })

        if tc_status != "passed":
            break

    run_result = {
        "status": overall_status,
        "job_id": job_id,
        "passed": sum(1 for r in results if r["status"] == "passed"),
        "total": len(test_cases),
        "results": results,
    }

    # 1. Cache result in Redis for polling fallback (5 min TTL)
    redis_client = ext.redis_client
    if redis_client:
        try:
            redis_client.setex(
                f"run_result:{job_id}",
                300,  # 5 minutes
                json.dumps(run_result),
            )
        except Exception as e:
            print(f"[Run Worker] Redis cache error (non-fatal): {e}")

    # 2. Emit result via SocketIO to user's personal room
    try:
        from app.sockets.events import emit_run_result
        emit_run_result(user_id, run_result)
    except Exception as e:
        print(f"[Run Worker] SocketIO emit error (non-fatal): {e}")

    print(f"[Run Worker] Job {job_id}: {overall_status}")


# Main Worker Loop

def run_worker():
    """
    Main worker loop — polls BOTH Redis queues:
    1. judge_queue (SUBMIT mode submissions)
    2. run_queue   (RUN mode sample test execution)

    BLPOP listens on both queues simultaneously.
    Spin up multiple instances for horizontal scaling.
    """
    app = create_app()
    executor = CodeExecutor(use_docker=True)

    print("=" * 60)
    print("[Judge Worker] Starting CodeArena Judge Worker")
    print(f"[Judge Worker] Docker mode: {executor.use_docker}")
    print("[Judge Worker] Listening on: judge_queue, run_queue")
    print("[Judge Worker] Waiting for jobs...")
    print("=" * 60)

    with app.app_context():
        redis_client = ext.redis_client

        while True:
            try:
                # BLPOP blocks until an item is available on EITHER queue
                # Priority: judge_queue first, then run_queue
                item = redis_client.blpop(
                    ["judge_queue", "run_queue"],
                    timeout=5,
                )

                if item is None:
                    continue  # Timeout, loop back

                queue_name, payload_str = item

                if queue_name == "judge_queue":
                    # SUBMIT mode — payload is a submission ID
                    submission_id = int(payload_str)
                    print(f"\n[Judge Worker] SUBMIT job: submission {submission_id}")
                    judge_submission(submission_id, executor)

                elif queue_name == "run_queue":
                    # RUN mode — payload is a JSON object
                    job_payload = json.loads(payload_str)
                    print(f"\n[Judge Worker] RUN job: {job_payload['job_id']}")
                    process_run_job(job_payload, executor)

            except KeyboardInterrupt:
                print("\n[Judge Worker] Shutting down...")
                break
            except Exception as e:
                print(f"[Judge Worker] Error: {e}")
                time.sleep(1)  # Avoid tight loop on repeated errors


if __name__ == "__main__":
    run_worker()
