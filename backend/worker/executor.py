"""
Code executor — runs user code inside a Docker container for safety.

Falls back to subprocess with timeout if Docker is not available (dev mode).
"""

import subprocess
import tempfile
import os
import time


class CodeExecutor:
    """Executes user code in a sandboxed environment."""

    def __init__(self, use_docker: bool = True, docker_image: str = "python:3.11-slim"):
        self.use_docker = use_docker
        self.docker_image = docker_image
        self._check_docker()

    def _check_docker(self) -> None:
        """Check if Docker is available. Fall back to subprocess if not."""
        if not self.use_docker:
            return
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True, timeout=5,
            )
            if result.returncode != 0:
                print("[Judge] Docker not available, falling back to subprocess mode")
                self.use_docker = False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("[Judge] Docker not available, falling back to subprocess mode")
            self.use_docker = False

    def execute(
        self,
        code: str,
        input_data: str,
        timeout: float = 5.0,
        memory_limit: str = "128m",
    ) -> dict:
        """
        Execute code with given input and return results.

        Returns:
            {
                "stdout": str,
                "stderr": str,
                "exit_code": int,
                "execution_time": float,
                "timed_out": bool,
            }
        """
        if self.use_docker:
            return self._execute_docker(code, input_data, timeout, memory_limit)
        else:
            return self._execute_subprocess(code, input_data, timeout)

    def _execute_docker(
        self,
        code: str,
        input_data: str,
        timeout: float,
        memory_limit: str,
    ) -> dict:
        """Execute code inside a Docker container."""
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = os.path.join(tmpdir, "solution.py")
            input_file = os.path.join(tmpdir, "input.txt")

            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(input_data)

            # Docker command with resource limits
            cmd = [
                "docker", "run",
                "--rm",
                "--network", "none",  # No network access
                "--memory", memory_limit,
                "--cpus", "1",
                "--pids-limit", "50",
                "-v", f"{tmpdir}:/workspace:ro",
                self.docker_image,
                "sh", "-c",
                f"cd /workspace && timeout {int(timeout)} python3 solution.py < input.txt",
            ]

            start_time = time.time()
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=timeout + 10,  # Extra buffer for Docker overhead
                    text=True,
                )
                execution_time = time.time() - start_time

                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "execution_time": execution_time,
                    "timed_out": result.returncode == 124,  # timeout exit code
                }
            except subprocess.TimeoutExpired:
                return {
                    "stdout": "",
                    "stderr": "Execution timed out",
                    "exit_code": -1,
                    "execution_time": timeout,
                    "timed_out": True,
                }

    def _execute_subprocess(
        self,
        code: str,
        input_data: str,
        timeout: float,
    ) -> dict:
        """
        Execute code via subprocess (development fallback).

        WARNING: This is NOT secure for production. Use Docker in production.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = os.path.join(tmpdir, "solution.py")

            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)

            start_time = time.time()
            try:
                result = subprocess.run(
                    ["python", code_file],
                    input=input_data,
                    capture_output=True,
                    timeout=timeout,
                    text=True,
                    cwd=tmpdir,
                )
                execution_time = time.time() - start_time

                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "execution_time": execution_time,
                    "timed_out": False,
                }
            except subprocess.TimeoutExpired:
                return {
                    "stdout": "",
                    "stderr": "Time limit exceeded",
                    "exit_code": -1,
                    "execution_time": timeout,
                    "timed_out": True,
                }
