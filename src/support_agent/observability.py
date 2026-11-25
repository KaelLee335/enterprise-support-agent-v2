"""Small JSON logging helpers with per-request trace correlation."""

import json
import logging
import re
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any
from langgraph.errors import GraphInterrupt
from support_agent.langfuse_observability import graph_node_observation

trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
agent_events_var: ContextVar[list[dict[str, Any]] | None] = ContextVar("agent_events", default=None)


def begin_agent_event_capture() -> ContextVar[list[dict[str, Any]] | None]:
    return agent_events_var.set([])


def finish_agent_event_capture(token: Any) -> list[dict[str, Any]]:
    events = agent_events_var.get() or []
    agent_events_var.reset(token)
    return list(events)


def _record_agent_event(event: dict[str, Any]) -> None:
    events = agent_events_var.get()
    if events is not None:
        if event.get("status") != "running" and events and events[-1].get("node") == event.get("node") and events[-1].get("status") == "running":
            events[-1] = {**events[-1], **event}
        else:
            events.append(event)

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_ -]?key|token|password|secret)(\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_CN_MOBILE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d[- ]?\d{4}[- ]?\d{4}(?!\d)")


def redact_user_input(value: str, *, limit: int = 500) -> str:
    """Return a bounded log preview with common credentials and contact data masked."""
    preview = value[:limit]
    for pattern in _SECRET_PATTERNS:
        preview = pattern.sub("[REDACTED]", preview)
    preview = _EMAIL.sub("[EMAIL]", preview)
    preview = _CN_MOBILE.sub("[PHONE]", preview)
    if len(value) > limit:
        preview += "…"
    return preview


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace_id = getattr(record, "trace_id", None) or trace_id_var.get()
        if trace_id:
            payload["trace_id"] = trace_id
        for key in (
            "event", "tenant_id", "intent", "source_count", "evidence_ids", "retrieved_sources",
            "error_type", "approval_status", "path", "status_code", "duration_ms",
            "node", "order_id", "order_status", "order_found", "citation_valid",
            "approval_decision", "question_preview",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def traced_node(name: str, node_fn):
    """Wrap a sync LangGraph node with correlated duration and safe I/O summaries."""
    import time

    logger = logging.getLogger("support_agent.agent.trace")

    def run(state: dict[str, Any]) -> dict[str, Any]:
        # Use the active HTTP request ID for resumed approval calls; fall back
        # to the original graph trace when invoked outside request context.
        trace_id = trace_id_var.get() or state.get("trace_id")
        started = time.perf_counter()
        common = {
            "node": name,
            "trace_id": trace_id,
            "tenant_id": state.get("tenant_id"),
            "intent": state.get("intent"),
            "order_id": state.get("order_id"),
        }
        logger.info("Agent node started", extra={"event": "node_start", **common})
        _record_agent_event({"node": name, "status": "running"})
        try:
            with graph_node_observation(name, intent=state.get("intent")) as observation:
                result = node_fn(state)
                if observation is not None:
                    try:
                        observation.update(output={
                            "status": "failed" if result.get("error") else "completed",
                            "evidence_ids": [item.get("source_id") for item in result.get("evidence", []) if isinstance(item, dict)],
                            "retrieved_sources": [
                                {"source_id": item.get("source_id"), "distance": item.get("distance")}
                                for item in result.get("evidence", []) if isinstance(item, dict)
                            ],
                            "order_found": result.get("order") is not None if "order" in result else None,
                            "order_status": (result.get("order") or {}).get("status") if isinstance(result.get("order"), dict) else None,
                            "citations_valid": result.get("citations_valid"),
                        })
                    except Exception:
                        logger.warning("Langfuse node metadata update failed; continuing", exc_info=True)
        except GraphInterrupt:
            logger.info(
                "Agent node paused for human input",
                extra={
                    "event": "node_pause", **common,
                    "approval_status": state.get("approval_status"),
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            _record_agent_event({"node": name, "status": "paused", "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
            raise
        except Exception as exc:
            logger.exception(
                "Agent node failed",
                extra={
                    "event": "node_error", **common,
                    "error_type": type(exc).__name__,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            _record_agent_event({"node": name, "status": "failed", "error_type": type(exc).__name__, "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
            raise

        summary: dict[str, Any] = {}
        if "order" in result:
            order = result.get("order")
            summary["order_found"] = order is not None
            if order:
                summary["order_status"] = order.get("status")
        if "evidence" in result:
            summary["source_count"] = len(result["evidence"])
            summary["evidence_ids"] = [item.get("source_id") for item in result["evidence"]]
            summary["retrieved_sources"] = [
                {"source_id": item.get("source_id"), "distance": item.get("distance")}
                for item in result["evidence"]
            ]
        for key in ("intent", "approval_status", "citations_valid"):
            if key in result:
                summary["citation_valid" if key == "citations_valid" else key] = result[key]
        if result.get("error"):
            summary["error_type"] = result["error"]
        logger.info(
            "Agent node finished",
            extra={
                "event": "node_end", **common, **summary,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        _record_agent_event({
            "node": name,
            "status": "completed" if not result.get("error") else "failed",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "evidence_ids": [item.get("source_id") for item in result.get("evidence", []) if isinstance(item, dict)],
        })
        return result

    return run
