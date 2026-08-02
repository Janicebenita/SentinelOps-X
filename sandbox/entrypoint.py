import os
import sys

allowed = {"pytest", "python", "ruff", "mypy", "bandit", "git"}
if not sys.argv[1:] or sys.argv[1] not in allowed:
    raise SystemExit("command rejected")
if sys.argv[1] == "git" and (len(sys.argv) < 3 or sys.argv[2] not in {"diff", "status", "show"}):
    raise SystemExit("git command rejected")
os.execvp(sys.argv[1], sys.argv[1:])
