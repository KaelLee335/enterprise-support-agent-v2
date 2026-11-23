from typing import Any, TypedDict


class SupportState(TypedDict, total=False):
    question: str
    trace_id: str
    tenant_id: str
    user_id: str
    user_role: str
    customer_id: str | None
    run_id: str
    database_path: str
    intent: str
    order_id: str | None
    clarify_reason: str | None
    refusal_reason: str | None
    order: dict[str, Any] | None
    shipment: dict[str, Any] | None
    platform_order: dict[str, Any] | None
    platform_logistics: dict[str, Any] | None
    aftersale_eligibility: dict[str, Any] | None
    evidence: list[dict[str, Any]]
    answer: str
    citations: list[str]
    citations_valid: bool
    error: str | None
    approval_ready: bool
    approval_status: str | None
    pending_action: dict[str, Any] | None
