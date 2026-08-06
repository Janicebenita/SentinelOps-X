from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..config import settings
from ..models import RoleVerification

PERMISSIONS = {
    "INTERN": ["view_workflows", "inspect_agents", "run_simulations", "inspect_evidence", "reject", "request_more_evidence"],
    "SENIOR_DEVELOPER": ["view_workflows", "inspect_agents", "run_simulations", "inspect_evidence", "approve", "reject", "request_more_evidence"],
}


class AuthError(ValueError):
    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message); self.code=code; self.message=message; self.status_code=status_code


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _secret() -> bytes:
    if settings.environment.lower() not in {"development", "test"} and settings.role_token_secret == "development-only-replace-me":
        raise RuntimeError("ROLE_TOKEN_SECRET must be configured outside development")
    return settings.role_token_secret.encode()


def _fingerprint(code: str) -> str:
    return hmac.new(_secret(), code.encode(), hashlib.sha256).hexdigest()[:16]


def verify_access_code(db: Session, actor_name: str, access_code: str) -> tuple[RoleVerification, str, list[str]]:
    role = None
    if hmac.compare_digest(access_code.encode(), settings.intern_access_code.encode()): role = "INTERN"
    if hmac.compare_digest(access_code.encode(), settings.senior_access_code.encode()): role = "SENIOR_DEVELOPER"
    if role is None: raise AuthError("INVALID_ACCESS_CODE", "Access code verification failed.", 401)
    now=datetime.now(timezone.utc); expires=now+timedelta(minutes=settings.role_token_expiry_minutes); token_id=secrets.token_hex(16)
    row=RoleVerification(actor_name=actor_name,role=role,verified=True,verified_at=now,expires_at=expires,token_id=token_id,code_fingerprint=_fingerprint(access_code)); db.add(row); db.commit(); db.refresh(row)
    payload={"sub":actor_name,"role":role,"exp":int(expires.timestamp()),"jti":token_id,"verification_id":row.id}
    header=_b64(json.dumps({"alg":"HS256","typ":"JWT"},separators=(",",":"),sort_keys=True).encode())
    body=_b64(json.dumps(payload,separators=(",",":"),sort_keys=True).encode()); signing=f"{header}.{body}"; signature=_b64(hmac.new(_secret(),signing.encode(),hashlib.sha256).digest())
    return row,f"{signing}.{signature}",PERMISSIONS[role]


def verify_token(db: Session, token: str) -> tuple[dict[str, Any], RoleVerification]:
    try: header,body,signature=token.split(".",2)
    except ValueError as exc: raise AuthError("INVALID_ROLE_TOKEN","Role verification token is invalid.",401) from exc
    try: header_payload=json.loads(_unb64(header))
    except (ValueError,json.JSONDecodeError) as exc: raise AuthError("INVALID_ROLE_TOKEN","Role verification token is invalid.",401) from exc
    if header_payload != {"alg":"HS256","typ":"JWT"}: raise AuthError("INVALID_ROLE_TOKEN","Role verification token is invalid.",401)
    expected=_b64(hmac.new(_secret(),f"{header}.{body}".encode(),hashlib.sha256).digest())
    if not hmac.compare_digest(signature,expected): raise AuthError("INVALID_ROLE_TOKEN","Role verification token is invalid.",401)
    try: payload=json.loads(_unb64(body))
    except (ValueError,json.JSONDecodeError) as exc: raise AuthError("INVALID_ROLE_TOKEN","Role verification token is invalid.",401) from exc
    if int(payload.get("exp",0)) <= int(datetime.now(timezone.utc).timestamp()): raise AuthError("ROLE_TOKEN_EXPIRED","Role verification has expired. Verify again.",401)
    row=db.get(RoleVerification,int(payload.get("verification_id",0)))
    if row is None or row.token_id != payload.get("jti") or not row.verified: raise AuthError("INVALID_ROLE_TOKEN","Role verification token is invalid.",401)
    return payload,row
