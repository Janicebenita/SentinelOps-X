# Security findings

Bandit reports **0 high**, **1 medium**, and 24 low-severity findings. B108 flags `HOME=/tmp` in the Docker command; this is intentional because `/tmp` is a bounded `tmpfs` mounted `noexec,nosuid`. Low findings are B101 test assertions, controlled subprocess calls (B603/B404), and one executable-path warning (B607).

All subprocesses use argument arrays and `shell=False`. Candidate execution is limited by an exact command allowlist. Docker candidate code has no network, bounded CPU/memory/process/time, a read-only root, and no Docker socket. Local Sandbox copies code to a disposable workspace and permits only predefined pytest commands. Protected paths, test deletion, assertion weakening, oversized patches, credentials, and network additions are rejected. PR creation requires recorded human approval; neither mode deploys.

Docker mode runs six gates. Local mode is a portability fallback running regression, unit, and integration pytest gates with reduced isolation and reports that distinction explicitly.
