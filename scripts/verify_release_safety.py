"""Produce a non-secret, machine-readable release safety summary for CI."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

from backend.app.config import settings
from backend.app.main import app

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROUTES = ("/deploy", "/scale", "/rollback", "/reconfigure", "/shell", "/production/execute")
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    "service_account_json": re.compile(r'"type"\s*:\s*"service_account"'),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "github_token": re.compile(r"gh[oprsu]_[0-9A-Za-z]{30,}"),
}
FRONTEND_FORBIDDEN = {
    "INTERN_ACCESS_CODE_NAME": "INTERN_ACCESS_CODE",
    "SENIOR_ACCESS_CODE_NAME": "SENIOR_ACCESS_CODE",
    "ROLE_TOKEN_SECRET_NAME": "ROLE_TOKEN_SECRET",
    "INTEGRATION_TOKEN_NAME": "INTEGRATION_TOKEN",
}
FRONTEND_ACCESS_CODES = {
    "INTERN_ACCESS_CODE_VALUE": settings.intern_access_code,
    "SENIOR_ACCESS_CODE_VALUE": settings.senior_access_code,
}


def source_files() -> Iterator[Path]:
    roots = [ROOT / "backend", ROOT / "frontend" / "src", ROOT / "scripts", ROOT / "docs", ROOT / ".github"]
    explicit = [ROOT / "pyproject.toml", ROOT / "cloudbuild.yaml", *ROOT.glob("Dockerfile.*")]
    seen: set[Path] = set()
    for base in [*roots, *explicit]:
        candidates = [base] if base.is_file() else base.rglob("*")
        for path in candidates:
            if path in seen or not path.is_file() or path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".yml", ".yaml", ".md", ".toml"}:
                continue
            seen.add(path)
            yield path


def main() -> None:
    paths = sorted(app.openapi()["paths"])
    forbidden_routes = [path for path in paths if any(term in path.lower() for term in FORBIDDEN_ROUTES)]
    source_findings: list[dict[str, str]] = []
    for path in source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                source_findings.append({"type": name, "file": str(path.relative_to(ROOT))})

    bundle_findings: list[str] = []
    dist = ROOT / "frontend" / "dist"
    if dist.exists():
        bundle = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in dist.rglob("*") if path.is_file())
        bundle_findings.extend(label for label, value in FRONTEND_FORBIDDEN.items() if value and value in bundle)
        credential_terms=r"intern|senior|access.?code|trial.?code|role"
        bundle_findings.extend(
            label for label, value in FRONTEND_ACCESS_CODES.items()
            if value and re.search(
                rf"(?i)(?:{credential_terms}).{{0,96}}{re.escape(value)}|{re.escape(value)}.{{0,96}}(?:{credential_terms})",
                bundle,
            )
        )
        for path in (ROOT / "frontend" / "src").rglob("*"):
            if not path.is_file() or ".test." in path.name or "test" in path.parts:
                continue
            text=path.read_text(encoding="utf-8",errors="ignore")
            bundle_findings.extend(
                label for label,value in FRONTEND_ACCESS_CODES.items()
                if value and re.search(rf"(?<!\d){re.escape(value)}(?!\d)",text)
            )
        bundle_findings.extend(name for name, pattern in SECRET_PATTERNS.items() if pattern.search(bundle))

    summary = {
        "production_action": "NOT_EXECUTED",
        "openapi_path_count": len(paths),
        "forbidden_routes": forbidden_routes,
        "source_secret_findings": source_findings,
        "frontend_bundle_findings": sorted(set(bundle_findings)),
        "frontend_bundle_scanned": dist.exists(),
    }
    output = ROOT / "security-reports" / "release-safety.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if forbidden_routes or source_findings or bundle_findings:
        raise SystemExit("Release safety verification failed")


if __name__ == "__main__":
    main()
