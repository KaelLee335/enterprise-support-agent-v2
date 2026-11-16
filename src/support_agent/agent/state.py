from typing import Any, TypedDict


class SupportState(TypedDict, total=False):
    question: str
    trace_id: str
    tenant_id: str
    user_id: str
    run_id: str
    database_path: str
    intent: str
    order_id: str | None
    clarify_reason: str | None
    refusal_reason: str | None
    order: dict[str, Any] | None
    evidence: list[dict[str, Any]]
    answer: str
    citations: list[str]
    citations_valid: bool
    error: str | None
    approval_ready: bool
    approval_status: str | None
    pending_action: dict[str, Any] | None
