import logging
import os
import time
import sqlite3
from uuid import uuid4
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from support_agent.agent.graph import build_support_graph
from support_agent.auth import DemoIdentity, require_demo_identity
from support_agent.config import get_settings
from support_agent.db import (
    create_agent_run,
    fetch_agent_run,
    fetch_order,
    initialize_database,
    update_agent_run,
)
from support_agent.schemas import (
    ApprovalDecision,
    ApprovalResponse,
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
            "question_preview": redact_user_input(chat_request.question),
        },
    )
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = request.app.state.support_graph.invoke({
            "question": chat_request.question,
            "tenant_id": identity.tenant_id,
            "user_id": identity.user_id,
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
    if values.get("approval_status") != "pending" or not snapshot.next:
        raise HTTPException(status_code=409, detail="Approval request is not pending")
    logger.info(
        "Demo approval decision received",
        extra={
            "event": "approval_decision", "trace_id": trace_id_var.get(),
            "tenant_id": identity.tenant_id,
            "user_id": identity.user_id,
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
