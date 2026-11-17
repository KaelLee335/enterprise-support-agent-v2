"""Fixed demo identities. Tokens are public examples, not production credentials."""

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from support_agent.config import get_settings


@dataclass(frozen=True)
class DemoIdentity:
    user_id: str
    tenant_id: str
    role: str = "requester"


_bearer = HTTPBearer(auto_error=False)


def require_demo_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> DemoIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Demo Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    identities = {
        settings.demo_token_demo_a: DemoIdentity("user-demo-a", "demo-a"),
        settings.demo_token_demo_a_approver: DemoIdentity(
            "user-demo-a-approver", "demo-a", "approver"
        ),
        settings.demo_token_legacy: DemoIdentity("user-legacy-demo", "legacy-demo"),
    }
    identity = identities.get(credentials.credentials)
    if identity is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid demo token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return identity
