"""Fixed demo identities. Tokens are public examples, not production credentials."""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from support_agent.config import get_settings


@dataclass(frozen=True)
class DemoIdentity:
    user_id: str
    tenant_id: str
    role: str = "customer"
    customer_id: str | None = None


_bearer = HTTPBearer(auto_error=False)


def require_demo_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> DemoIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Demo Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = getattr(request.app.state, "settings", get_settings())
    identities = {
        settings.demo_token_demo_a: ("user-demo-a", "demo-a"),
        settings.demo_token_demo_b: ("user-demo-b", "demo-b"),
        settings.demo_token_demo_a_approver: ("user-demo-a-approver", "demo-a"),
        settings.demo_token_demo_a_approver_alt: ("user-demo-a-approver-alt", "demo-a"),
        settings.demo_token_legacy: ("user-legacy-demo", "legacy-demo"),
        settings.demo_token_demo_a_service: ("user-demo-a-service", "demo-a"),
        settings.demo_token_demo_a_admin: ("user-demo-a-admin", "demo-a"),
    }
    subject = identities.get(credentials.credentials)
    if subject is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid demo token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if isinstance(subject, DemoIdentity):
        user_id, tenant_id = subject.user_id, subject.tenant_id
    else:
        user_id, tenant_id = subject
    # Role and customer binding come from the server-side tenant membership table,
    # never from caller-controlled headers or request fields.
    from support_agent.db import fetch_tenant_user

    membership = fetch_tenant_user(settings.database_path, tenant_id, user_id)
    if membership is None or not membership["is_active"]:
        raise HTTPException(status_code=401, detail="Demo identity is not active")
    return DemoIdentity(
        user_id=user_id,
        tenant_id=tenant_id,
        role=membership["role"],
        customer_id=membership["customer_id"],
    )
