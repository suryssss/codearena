"""
Background judge consumer — runs inside the Flask process for development.

In production, use the standalone worker: `python -m worker.judge`
This module starts a daemon thread that polls the Redis judge_queue
and processes submissions using the CodeExecutor (subprocess mode).
"""

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
        """Poll Redis queue and judge submissions."""
        from worker.executor import CodeExecutor
        from worker.judge import judge_submission

        executor = CodeExecutor(use_docker=False)
        app.logger.info("[BG Judge] Background judge consumer started (subprocess mode)")

        while True:
            try:
                redis_client = ext.redis_client
                if not redis_client:
                    time.sleep(5)
                    continue

                # BLPOP blocks until an item is available (timeout 3s)
                item = redis_client.blpop("judge_queue", timeout=3)

                if item is None:
                    continue  # Timeout, loop back

                _, submission_id_str = item
                submission_id = int(submission_id_str)
                app.logger.info(f"[BG Judge] Processing submission {submission_id}")

                with app.app_context():
                    judge_submission(submission_id, executor)

                app.logger.info(f"[BG Judge] Finished submission {submission_id}")

            except Exception as e:
                app.logger.error(f"[BG Judge] Error: {e}")
                time.sleep(2)  # Avoid tight loop on errors

    thread = threading.Thread(target=consumer, name="bg-judge-consumer", daemon=True)
    thread.start()
