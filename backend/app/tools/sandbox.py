from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

ALLOWED = {"pytest", "python", "ruff", "mypy", "bandit", "git"}
META = re.compile(r"[;&|`$<>\n\r]")
LOCAL_PYTEST_COMMANDS = {
    ("pytest", "-q", "demo_app/tests/test_regression_checkout.py"),
    ("pytest", "demo_app/tests/test_regression_checkout.py"),
    ("pytest", "demo_app/tests"),
    ("pytest", "backend/tests", "demo_app/tests"),
}
COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "node_modules",
    "dist",
    ".venv",
    "*.db",
    ".mypy_cache",
    ".pytest_cache",
    ".pytest-tmp",
    ".pytest-tmp-*",
    ".runtime-tmp-*",
    ".ruff_cache",
    ".pnpm-store",
    ".coverage",
)


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    timed_out: bool = False


class Sandbox(Protocol):
    """Common execution boundary for candidate-code verification."""

    mode: str

    def run(self, command: list[str], workspace: str, timeout: int = 90) -> CommandResult:
        """Run an allowlisted command in an isolated workspace."""


def validate_command(command: list[str]) -> None:
    if not command or command[0] not in ALLOWED:
        raise ValueError("Command is not allowlisted")
    if any(META.search(arg) for arg in command):
        raise ValueError("Shell metacharacters are forbidden")
    if command[0] == "git" and (len(command) < 2 or command[1] not in {"diff", "status", "show"}):
        raise ValueError("Git command is not read-only")


def _timeout_result(exc: subprocess.TimeoutExpired, started: float) -> CommandResult:
    stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
    stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    return CommandResult(stdout, stderr, 124, time.perf_counter() - started, True)


class DockerSandbox:
    """Run checks in the restricted, network-disabled Docker image."""

    mode = "docker"

    def __init__(self, image: str = "sentinelops-sandbox:latest") -> None:
        self.image = image

    def run(self, command: list[str], workspace: str, timeout: int = 90) -> CommandResult:
        validate_command(command)
        started = time.perf_counter()
        docker = [
            "docker", "run", "--rm", "--network=none", "--cpus=1", "--memory=512m",
            "--pids-limit=128", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=128m",
        ]
        getuid = getattr(os, "getuid", None)
        getgid = getattr(os, "getgid", None)
        if callable(getuid) and callable(getgid):
            docker.extend(["--user", f"{getuid()}:{getgid()}"])
        docker.extend([
            "-e", "HOME=/tmp", "-v", f"{workspace}:/workspace:rw", "-w", "/workspace",
            self.image, *command,
        ])
        try:
            result = subprocess.run(docker, text=True, capture_output=True, timeout=timeout, check=False)
            return CommandResult(result.stdout, result.stderr, result.returncode, time.perf_counter() - started)
        except OSError as exc:
            return CommandResult("", f"Sandbox unavailable: {exc}", 127, time.perf_counter() - started)
        except subprocess.TimeoutExpired as exc:
            return _timeout_result(exc, started)


class LocalSandbox:
    """Docker-free fallback limited to exact, predefined pytest invocations."""

    mode = "local"

    def run(self, command: list[str], workspace: str, timeout: int = 90) -> CommandResult:
        validate_command(command)
        if tuple(command) not in LOCAL_PYTEST_COMMANDS:
            raise ValueError("Local sandbox only permits predefined pytest commands")
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="sentinelops-local-sandbox-") as temp:
            isolated = Path(temp) / "workspace"
            shutil.copytree(workspace, isolated, ignore=COPY_IGNORE)
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", *command[1:]],
                    cwd=isolated,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                    shell=False,
                )
                return CommandResult(
                    result.stdout, result.stderr, result.returncode, time.perf_counter() - started
                )
            except subprocess.TimeoutExpired as exc:
                return _timeout_result(exc, started)


def docker_available() -> bool:
    """Return whether a Docker client is installed on this host."""

    return shutil.which("docker") is not None


def get_sandbox(image: str = "sentinelops-sandbox:latest") -> Sandbox:
    """Select the strongest sandbox supported by the current environment."""

    return DockerSandbox(image) if docker_available() else LocalSandbox()


def docker_run(
    command: list[str], workspace: str, image: str = "sentinelops-sandbox:latest", timeout: int = 90
) -> CommandResult:
    """Backward-compatible automatic sandbox entry point."""

    return get_sandbox(image).run(command, workspace, timeout)
