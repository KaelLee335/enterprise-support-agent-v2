from typing import Any

from pydantic import BaseModel, Field
from typing import Literal


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class EvidenceResponse(BaseModel):
    source_id: str
    title: str
    content: str
    distance: float


class ChatResponse(BaseModel):
    answer: str
    intent: str
    order: dict[str, Any] | None = None
    shipment: dict[str, Any] | None = None
    platform_order: dict[str, Any] | None = None
    platform_logistics: dict[str, Any] | None = None
    aftersale_eligibility: dict[str, Any] | None = None
    evidence: list[EvidenceResponse] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    citations_valid: bool | None = None
    error: str | None = None
    thread_id: str
    run_id: str
    trace_id: str
    approval_status: str | None = None
    pending_action: dict[str, Any] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    approved: bool


class ApprovalAssignmentRequest(BaseModel):
    approver_id: str = Field(min_length=1, max_length=128)


class TenantUserRoleRequest(BaseModel):
    role: Literal["customer", "service", "approver", "admin"]
    customer_id: str | None = None


class ApprovalResponse(BaseModel):
    thread_id: str
    approval_status: str
    answer: str
    pending_action: dict[str, Any] | None = None
    error: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    question: str | None = None
    order: dict[str, Any] | None = None
    evidence: list[EvidenceResponse] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


class AgentFeedback(BaseModel):
    run_id: str = Field(min_length=1, max_length=64)
    label: Literal["helpful", "unhelpful", "incorrect", "unsupported"]


class OrderResponse(BaseModel):
    order_id: str
    tenant_id: str
    customer_id: str | None = None
    product: str
    product_type: str | None = None
    is_customized: bool
    quantity: int
    amount_cents: int | None = None
    currency: str
    status: str
    created_date: str | None = None
    paid_date: str | None = None
    shipped_date: str | None = None
    received_date: str | None = None
    feedback_date: str | None = None
    issue_description: str | None = None
    refund_started_date: str | None = None
    refund_completed_date: str | None = None
    is_demo: bool


class AftersaleCreateRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=128)
    confirmed: bool = False


class DemoAftersaleResponse(BaseModel):
    request_id: str
    aftersale_id: str | None = None
    order_id: str
    status: str
    message: str
    demo_only: bool = True


class WebhookReceiptResponse(BaseModel):
    event_id: str
    event_type: str
    order_id: str
    order_status: str
    duplicate: bool
    demo_only: bool = True


class AgentRunResponse(BaseModel):
    run_id: str
    trace_id: str
    user_id: str
    tenant_id: str
    intent: str | None = None
    status: str
    error_type: str | None = None
    started_at: str
    finished_at: str | None = None
    is_demo: bool
