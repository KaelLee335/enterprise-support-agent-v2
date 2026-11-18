import logging
import hashlib
import hmac
import os
import time
import sqlite3
from uuid import uuid4
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import ValidationError
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from support_agent.agent.graph import build_support_graph
from support_agent.auth import DemoIdentity, require_demo_identity
from support_agent.config import get_settings
from support_agent.db import (
    AftersaleIdempotencyConflict,
    create_agent_run,
    fetch_aftersale_request,
    fetch_agent_run,
    fetch_order,
    fetch_webhook_event,
    initialize_database,
    reserve_aftersale_request,
    update_agent_run,
    update_aftersale_request,
    process_mockshop_webhook,
    WebhookEventConflict,
)
from support_agent.integrations.errors import IntegrationError, IntegrationNotFound
from support_agent.integrations.factory import create_mock_shop_adapter
from support_agent.integrations.mock_shop import MockShopAdapter
from support_agent.integrations.models import AftersaleEligibility, LogisticsInfo, PlatformOrder
from support_agent.integrations.mock_shop import normalize_order_status
from support_agent.integrations.webhooks import MockShopWebhookEvent, normalized_order_status
from support_agent.integrations.permissions import apply_webhook_order_state, can_access_order, tenant_for_store
from support_agent.schemas import (
    ApprovalDecision,
    ApprovalResponse,
    AftersaleCreateRequest,
    DemoAftersaleResponse,
    WebhookReceiptResponse,
    AgentRunResponse,
    ChatRequest,
    ChatResponse,
    OrderResponse,
)
from support_agent.observability import configure_logging, redact_user_input, trace_id_var

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
def _resolve_seed_path() -> Path:
    """seed 文件路径解析：源码布局、site-packages 安装、容器内三种场景都要能找到。

    - 源码布局：src/support_agent/main.py → parents[2] = 项目根/data/seed
    - pip 安装后：site-packages 下 parents[2] 不含 data，回退到 CWD/data/seed
      （容器 WORKDIR=/app，Dockerfile 已 COPY data/seed → /app/data/seed）
    - SEED_PATH 环境变量可显式覆盖，优先级最高
    """
    candidates = []
    env_seed = os.environ.get("SEED_PATH")
    if env_seed:
        candidates.append(Path(env_seed))
    candidates.append(Path(__file__).resolve().parents[2] / "data" / "seed" / "v1_orders.json")
    candidates.append(Path.cwd() / "data" / "seed" / "v1_orders.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"seed 文件未找到，尝试过：{[str(c) for c in candidates]}"
    )


SEED_PATH = _resolve_seed_path()


def _open_checkpoint_connection(path: Path) -> sqlite3.Connection:
    """Open a checkpoint DB only after a read-only integrity preflight.

    Corrupt checkpoint state may contain pending approvals. Fail startup without
    replacing or mutating that file so an operator can preserve and inspect it.
    """
    connection = sqlite3.connect(path, check_same_thread=False)
    try:
        result = connection.execute("PRAGMA quick_check").fetchone()
    except sqlite3.DatabaseError as exc:
        connection.close()
        raise RuntimeError(
            "Checkpoint database is corrupt or unreadable; the file was preserved."
        ) from exc
    if result is None or result[0] != "ok":
        connection.close()
        raise RuntimeError(
            "Checkpoint database failed its integrity check; the file was preserved."
        )
    return connection


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    connection = _open_checkpoint_connection(settings.checkpoint_path)
    try:
        initialize_database(settings.database_path, SEED_PATH)
        checkpointer = SqliteSaver(connection)
        application.state.support_graph = build_support_graph(checkpointer)
        yield
    finally:
        connection.close()


app = FastAPI(
    title="Enterprise Support Agent V2",
    version="0.1.0",
    description="Local demo API for tenant-scoped, read-only order lookup.",
    lifespan=lifespan,
)


@app.middleware("http")
async def trace_requests(request: Request, call_next):
    trace_id = uuid4().hex
    token = trace_id_var.set(trace_id)
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Trace-ID"] = trace_id
        return response
    finally:
        logger.info(
            "HTTP request completed",
            extra={
                "event": "http_request", "trace_id": trace_id, "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        trace_id_var.reset(token)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _new_mock_shop_adapter() -> MockShopAdapter:
    return create_mock_shop_adapter(settings)


def _load_authorized_platform_order(adapter: MockShopAdapter, order_id: str, identity: DemoIdentity):
    try:
        order = adapter.get_order(order_id)
    except IntegrationNotFound as exc:
        raise HTTPException(status_code=404, detail="Order not found for this identity") from exc
    except IntegrationError as exc:
        logger.warning(
            "Mock platform order lookup failed",
            extra={"event": "platform_call_failed", "trace_id": trace_id_var.get(),
                   "tenant_id": identity.tenant_id, "platform": adapter.platform_name,
                   "error_code": exc.code},
        )
        raise HTTPException(status_code=503, detail="Demo commerce service is temporarily unavailable") from exc
    if not can_access_order(identity, order):
        raise HTTPException(status_code=404, detail="Order not found for this identity")
    return apply_webhook_order_state(order, settings.database_path)


@app.get("/ecommerce/orders/{order_id}", response_model=PlatformOrder)
def get_ecommerce_order(
    order_id: str,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> PlatformOrder:
    adapter = _new_mock_shop_adapter()
    try:
        order = _load_authorized_platform_order(adapter, order_id, identity)
        return order
    finally:
        adapter.close()


@app.get("/ecommerce/orders/{order_id}/logistics", response_model=LogisticsInfo)
def get_ecommerce_logistics(
    order_id: str,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> LogisticsInfo:
    adapter = _new_mock_shop_adapter()
    try:
        _load_authorized_platform_order(adapter, order_id, identity)
        try:
            return adapter.get_logistics(order_id)
        except IntegrationNotFound as exc:
            raise HTTPException(status_code=404, detail="Logistics not found") from exc
        except IntegrationError as exc:
            logger.warning(
                "Mock platform logistics lookup failed",
                extra={"event": "platform_call_failed", "trace_id": trace_id_var.get(),
                       "tenant_id": identity.tenant_id, "platform": adapter.platform_name,
                       "error_code": exc.code},
            )
            raise HTTPException(status_code=503, detail="Demo commerce service is temporarily unavailable") from exc
    finally:
        adapter.close()


@app.get("/ecommerce/orders/{order_id}/aftersale-eligibility", response_model=AftersaleEligibility)
def get_ecommerce_aftersale_eligibility(
    order_id: str,
    reason: str = "售后咨询（演示）",
    identity: DemoIdentity = Depends(require_demo_identity),
) -> AftersaleEligibility:
    adapter = _new_mock_shop_adapter()
    try:
        _load_authorized_platform_order(adapter, order_id, identity)
        try:
            return adapter.check_aftersale_eligibility(order_id, reason)
        except IntegrationNotFound as exc:
            raise HTTPException(status_code=404, detail="Order not found for this identity") from exc
        except IntegrationError as exc:
            logger.warning(
                "Mock platform aftersale check failed",
                extra={"event": "platform_call_failed", "trace_id": trace_id_var.get(),
                       "tenant_id": identity.tenant_id, "platform": adapter.platform_name,
                       "error_code": exc.code},
            )
            raise HTTPException(status_code=503, detail="Demo commerce service is temporarily unavailable") from exc
    finally:
        adapter.close()


@app.post("/ecommerce/orders/{order_id}/aftersales", response_model=DemoAftersaleResponse)
def create_ecommerce_aftersale(
    order_id: str,
    body: AftersaleCreateRequest,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> DemoAftersaleResponse:
    if identity.role != "requester":
        raise HTTPException(status_code=403, detail="Demo requester role required")
    if not body.confirmed:
        raise HTTPException(status_code=409, detail="Explicit demo confirmation is required before submitting")

    adapter = _new_mock_shop_adapter()
    try:
        order = _load_authorized_platform_order(adapter, order_id, identity)
        scoped_key = hashlib.sha256(
            f"{identity.tenant_id}:{body.idempotency_key}".encode("utf-8")
        ).hexdigest()
        try:
            record, created_now = reserve_aftersale_request(
                settings.database_path,
                request_id=uuid4().hex,
                tenant_id=identity.tenant_id,
                user_id=identity.user_id,
                order_id=order_id,
                platform=adapter.platform_name,
                reason=body.reason,
                idempotency_key=body.idempotency_key,
            )
        except AftersaleIdempotencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not created_now:
            if record["status"] == "pending_demo":
                return DemoAftersaleResponse(
                    request_id=record["request_id"],
                    aftersale_id=record["platform_aftersale_id"], order_id=order_id,
                    status="pending_demo",
                    message="已返回同一幂等键对应的演示申请；未执行退款或退货。",
                )
            if record["status"] == "submitting":
                raise HTTPException(status_code=409, detail="A request with this idempotency key is in progress")
            update_aftersale_request(
                settings.database_path, record["request_id"], identity.tenant_id,
                status="submitting",
            )
        try:
            eligibility = adapter.check_aftersale_eligibility(order_id, body.reason)
        except IntegrationError as exc:
            update_aftersale_request(
                settings.database_path, record["request_id"], identity.tenant_id,
                status="failed",
            )
            raise HTTPException(status_code=503, detail="Demo commerce service is temporarily unavailable") from exc
        if not eligibility.eligible:
            update_aftersale_request(
                settings.database_path, record["request_id"], identity.tenant_id,
                status="failed",
            )
            raise HTTPException(status_code=409, detail=eligibility.explanation)
        try:
            application = adapter.create_aftersale(order_id, body.reason, scoped_key)
        except IntegrationError as exc:
            update_aftersale_request(
                settings.database_path, record["request_id"], identity.tenant_id,
                status="failed",
            )
            logger.warning(
                "Mock platform aftersale submission failed",
                extra={"event": "platform_call_failed", "trace_id": trace_id_var.get(),
                       "tenant_id": identity.tenant_id, "user_id": identity.user_id,
                       "order_id": order_id, "platform": adapter.platform_name,
                       "error_code": exc.code},
            )
            raise HTTPException(status_code=503, detail="Demo aftersale submission failed") from exc
        update_aftersale_request(
            settings.database_path, record["request_id"], identity.tenant_id,
            status="pending_demo", platform_aftersale_id=application.aftersale_id,
        )
        logger.info(
            "Demo aftersale request created",
            extra={"event": "demo_aftersale_created", "trace_id": trace_id_var.get(),
                   "tenant_id": identity.tenant_id, "user_id": identity.user_id,
                   "order_id": order.order_id, "platform": adapter.platform_name,
                   "request_id": record["request_id"], "status": "pending_demo"},
        )
        return DemoAftersaleResponse(
            request_id=record["request_id"], aftersale_id=application.aftersale_id,
            order_id=order_id, status="pending_demo",
            message="已创建 MockShop 演示售后申请，状态为待处理；这不代表已审批、退货或退款。",
        )
    finally:
        adapter.close()


@app.get("/ecommerce/aftersales/{request_id}", response_model=DemoAftersaleResponse)
def get_ecommerce_aftersale(
    request_id: str,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> DemoAftersaleResponse:
    record = fetch_aftersale_request(settings.database_path, request_id, identity.tenant_id)
    if record is None or (identity.role != "approver" and record["user_id"] != identity.user_id):
        raise HTTPException(status_code=404, detail="Aftersale request not found")
    return DemoAftersaleResponse(
        request_id=record["request_id"], aftersale_id=record["platform_aftersale_id"],
        order_id=record["order_id"], status=record["status"],
        message="本地 Demo 申请状态；不代表平台已执行退款或退货。",
    )


@app.post("/webhooks/mock-shop", response_model=WebhookReceiptResponse)
async def receive_mockshop_webhook(
    request: Request,
    signature: str | None = Header(default=None, alias="X-MockShop-Signature"),
) -> WebhookReceiptResponse:
    # Header is read explicitly from the request; only the signature and raw body
    # participate in authentication. The event cannot choose its tenant.
    raw_body = await request.body()
    provided_signature = signature or ""
    if len(raw_body) > 32_768:
        raise HTTPException(status_code=413, detail="Webhook payload too large")
    expected_signature = "sha256=" + hmac.new(
        settings.mock_shop_webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        event = MockShopWebhookEvent.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid MockShop webhook event") from exc
    tenant_id = tenant_for_store(event.shop_id)
    if tenant_id is None:
        raise HTTPException(status_code=404, detail="Unknown demo store")
    try:
        order_status = normalized_order_status(event)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Unsupported MockShop event state") from exc
    try:
        state, created = process_mockshop_webhook(
            settings.database_path,
            event_id=event.event_id,
            event_type=event.event_type,
            tenant_id=tenant_id,
            store_id=event.shop_id,
            order_id=event.order_id,
            customer_id=event.customer_id,
            platform_status=event.platform_status,
            occurred_at=event.occurred_at.isoformat(),
            payload_sha256=hashlib.sha256(raw_body).hexdigest(),
        )
    except WebhookEventConflict as exc:
        raise HTTPException(status_code=409, detail="Webhook event id conflicts with a prior payload") from exc
    logger.info(
        "MockShop webhook processed",
        extra={"event": "mockshop_webhook", "trace_id": trace_id_var.get(),
               "tenant_id": tenant_id, "store_id": event.shop_id,
               "order_id": event.order_id, "event_id": event.event_id,
               "event_type": event.event_type, "duplicate": not created,
               "order_status": normalize_order_status(state["platform_status"])},
    )
    return WebhookReceiptResponse(
        event_id=event.event_id, event_type=event.event_type,
        order_id=event.order_id,
        order_status=normalize_order_status(state["platform_status"]),
        duplicate=not created,
    )


@app.get("/webhooks/mock-shop/events/{event_id}")
def get_mockshop_webhook_event(
    event_id: str,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> dict:
    event = fetch_webhook_event(settings.database_path, event_id, identity.tenant_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Webhook event not found")
    return {
        "event_id": event["event_id"], "event_type": event["event_type"],
        "order_id": event["order_id"], "status": event["status"],
        "received_at": event["received_at"], "demo_only": True,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(
    chat_request: ChatRequest,
    request: Request,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> ChatResponse:
    trace_id = trace_id_var.get() or uuid4().hex
    thread_id = uuid4().hex
    run_id = uuid4().hex
    create_agent_run(
        settings.database_path, run_id, trace_id, identity.user_id, identity.tenant_id
    )
    logger.info(
        "Agent run started",
        extra={
            "event": "agent_start", "trace_id": trace_id,
            "tenant_id": identity.tenant_id,
            "user_id": identity.user_id,
            "user_role": identity.role,
            "question_preview": redact_user_input(chat_request.question),
        },
    )
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = request.app.state.support_graph.invoke({
            "question": chat_request.question,
            "tenant_id": identity.tenant_id,
            "user_id": identity.user_id,
            "user_role": identity.role,
            "database_path": str(settings.database_path),
            "thread_id": thread_id,
            "run_id": run_id,
            "trace_id": trace_id,
        }, config=config)
    except Exception as exc:
        update_agent_run(
            settings.database_path,
            run_id,
            identity.tenant_id,
            status="failed",
            error_type=type(exc).__name__,
        )
        logger.exception("Agent run failed")
        raise
    approval_status = state.get("approval_status")
    run_status = (
        "pending" if approval_status == "pending"
        else "failed" if state.get("error")
        else "completed"
    )
    update_agent_run(
        settings.database_path,
        run_id,
        identity.tenant_id,
        status=run_status,
        intent=state.get("intent"),
        error_type=state.get("error"),
    )
    return ChatResponse(
        answer=state.get("answer", "暂时无法处理该请求。"),
        intent=state.get("intent", "unknown"),
        order=state.get("order"),
        shipment=state.get("shipment"),
        platform_order=state.get("platform_order"),
        platform_logistics=state.get("platform_logistics"),
        aftersale_eligibility=state.get("aftersale_eligibility"),
        evidence=state.get("evidence", []),
        citations=state.get("citations", []),
        citations_valid=state.get("citations_valid"),
        error=state.get("error"),
        thread_id=thread_id,
        run_id=run_id,
        trace_id=trace_id,
        approval_status=state.get("approval_status"),
        pending_action=state.get("pending_action"),
    )


def _approval_snapshot(thread_id: str, tenant_id: str):
    graph = app.state.support_graph
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if not snapshot.values or snapshot.values.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return graph, config, snapshot


@app.get("/approvals/{thread_id}", response_model=ApprovalResponse)
def get_approval(
    thread_id: str,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> ApprovalResponse:
    _, _, snapshot = _approval_snapshot(thread_id, identity.tenant_id)
    values = snapshot.values
    return ApprovalResponse(
        thread_id=thread_id,
        approval_status=values.get("approval_status", "not_pending"),
        answer=values.get("answer", ""),
        pending_action=values.get("pending_action"),
        error=values.get("error"),
    )


@app.post("/approvals/{thread_id}/decision", response_model=ApprovalResponse)
def decide_approval(
    thread_id: str,
    decision: ApprovalDecision,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> ApprovalResponse:
    graph, config, snapshot = _approval_snapshot(thread_id, identity.tenant_id)
    values = snapshot.values
    if identity.role != "approver":
        raise HTTPException(status_code=403, detail="Demo approver role required")
    if values.get("user_id") == identity.user_id:
        raise HTTPException(status_code=403, detail="Requester cannot approve own request")
    if values.get("approval_status") != "pending" or not snapshot.next:
        raise HTTPException(status_code=409, detail="Approval request is not pending")
    logger.info(
        "Demo approval decision received",
        extra={
            "event": "approval_decision", "trace_id": trace_id_var.get(),
            "tenant_id": identity.tenant_id,
            "user_id": identity.user_id,
            "user_role": identity.role,
            "requester_user_id": values.get("user_id"),
            "thread_id": thread_id,
            "approval_status": "approved_demo" if decision.approved else "rejected",
            "approval_decision": decision.approved,
        },
    )
    result = graph.invoke(Command(resume={"approved": decision.approved}), config=config)
    run_id = result.get("run_id")
    if run_id:
        update_agent_run(
            settings.database_path,
            run_id,
            identity.tenant_id,
            status="completed",
            intent=result.get("intent"),
            error_type=result.get("error"),
        )
    return ApprovalResponse(
        thread_id=thread_id,
        approval_status=result.get("approval_status", "unknown"),
        answer=result.get("answer", "Approval decision recorded."),
        pending_action=result.get("pending_action"),
        error=result.get("error"),
    )


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> OrderResponse:
    logger.info("Order lookup requested order_id=%s tenant_id=%s", order_id, identity.tenant_id)
    order = fetch_order(settings.database_path, order_id, identity.tenant_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found for this tenant")
    return OrderResponse(**order)


@app.get("/agent-runs/{run_id}", response_model=AgentRunResponse)
def get_agent_run_endpoint(
    run_id: str,
    identity: DemoIdentity = Depends(require_demo_identity),
) -> AgentRunResponse:
    run = fetch_agent_run(settings.database_path, run_id, identity.tenant_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return AgentRunResponse(**run)
