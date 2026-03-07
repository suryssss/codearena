"""
Background judge consumer — runs inside the Flask process for development.

In production, use the standalone worker: `python -m worker.judge`
This module starts a daemon thread that polls BOTH Redis queues
(judge_queue and run_queue) and processes them using the CodeExecutor.
"""

import json
import threading
import time
import app.extensions as ext


_worker_started = False
_worker_lock = threading.Lock()


def start_background_judge(app):
    """
    Start the background judge consumer thread.
    Safe to call multiple times — only starts once.
    """
    global _worker_started

    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True

    if not ext.redis_client:
        app.logger.info("[BG Judge] Redis not available, skipping background judge")
        return

    def consumer():
        """Poll Redis queues and process submissions + run jobs."""
        from worker.executor import CodeExecutor
        from worker.judge import judge_submission, process_run_job

        executor = CodeExecutor(use_docker=False)
        app.logger.info("[BG Judge] Background judge consumer started (subprocess mode)")
        app.logger.info("[BG Judge] Listening on: judge_queue, run_queue")

        while True:
            try:
                redis_client = ext.redis_client
                if not redis_client:
                    time.sleep(5)
                    continue

                # BLPOP blocks until an item is available on EITHER queue
                item = redis_client.blpop(
                    ["judge_queue", "run_queue"],
                    timeout=3,
                )

                if item is None:
                    continue  # Timeout, loop back

                queue_name, payload_str = item

                with app.app_context():
                    if queue_name == "judge_queue":
                        submission_id = int(payload_str)
                        app.logger.info(f"[BG Judge] Processing SUBMIT: submission {submission_id}")
                        judge_submission(submission_id, executor)
                        app.logger.info(f"[BG Judge] Finished submission {submission_id}")

                    elif queue_name == "run_queue":
                        job_payload = json.loads(payload_str)
                        app.logger.info(f"[BG Judge] Processing RUN: job {job_payload['job_id']}")
                        process_run_job(job_payload, executor)
                        app.logger.info(f"[BG Judge] Finished run job {job_payload['job_id']}")

            except Exception as e:
                app.logger.error(f"[BG Judge] Error: {e}")
                time.sleep(2)  # Avoid tight loop on errors

    thread = threading.Thread(target=consumer, name="bg-judge-consumer", daemon=True)
    thread.start()
