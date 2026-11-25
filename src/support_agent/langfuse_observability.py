"""Opt-in Langfuse tracing for the existing LangGraph request.

The local graph event timeline remains available without this external SDK.
Sensitive LLM/tool input and output are replaced before export; Langfuse receives
only structural telemetry and the minimum identifiers needed to join one run.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

logger = logging.getLogger(__name__)
_active_client: ContextVar[Any | None] = ContextVar("langfuse_active_client", default=None)
_PII_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d[- ]?\d{4}[- ]?\d{4}(?!\d)"),
)


def redact_text(value: str) -> str:
    for pattern in _PII_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value[:500]


def mask_export_batch(*, params):
    """Strip raw prompt/response text and redact common PII in exported spans."""
    from langfuse import MaskOtelSpansResult, OtelSpanPatch

    patches = {}
    for identifier, span in params.spans.items():
        replacements = {}
        for key, value in span.attributes.items():
            if not isinstance(value, str):
                continue
            if any(marker in key.lower() for marker in ("input", "output", "prompt", "completion", "content", "message")):
                replacements[key] = "[REDACTED]"
                continue
            masked = redact_text(value)
            if masked != value:
                replacements[key] = masked
        if replacements:
            patches[identifier] = OtelSpanPatch(set_attributes=replacements)
    return MaskOtelSpansResult(span_patches=patches) if patches else None


def langfuse_status(settings: Any) -> dict[str, Any]:
    enabled = bool(settings.langfuse_enabled)
    credentials = bool(settings.langfuse_public_key and settings.langfuse_secret_key)
    return {
        "enabled": enabled and credentials,
        "requested": enabled,
        "configured": credentials,
        "base_url": settings.langfuse_base_url,
        "reason": "ready" if enabled and credentials else "disabled" if not enabled else "missing_credentials",
    }


def build_handler(settings: Any):
    """Create the official LangChain callback only when opt-in config is complete."""
    if not langfuse_status(settings)["enabled"]:
        return None
    try:
        _configure_langfuse_client(settings)
        from langfuse.langchain import CallbackHandler

        return CallbackHandler()
    except Exception:
        logger.exception("Langfuse callback initialization failed; continuing without export")
        return None


@lru_cache(maxsize=1)
def _configure_langfuse_client(settings: Any):
    from langfuse import Langfuse

    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url,
        mask_otel_spans=mask_export_batch,
    )


@contextmanager
def request_observation(settings: Any, *, trace_id: str, thread_id: str, run_id: str,
                        user_scope: str) -> Iterator[tuple[Any, list[Any]]]:
    """Create an explicit request parent; yield handler list, or no-op when off.

    SDK setup errors are fail-open. Graph exceptions are deliberately not swallowed.
    """
    handler = build_handler(settings)
    if handler is None:
        yield None, []
        return
    try:
        _configure_langfuse_client(settings)
        from langfuse import get_client, propagate_attributes

        client = get_client()
        observation_scope = client.start_as_current_observation(
            as_type="span", name="support-agent-request",
            trace_context={"trace_id": trace_id},
        )
        observation = observation_scope.__enter__()
        attrs_scope = propagate_attributes(session_id=thread_id, user_id=user_scope)
        attrs_scope.__enter__()
        observation.update(
            input={"content": "[REDACTED]"},
            metadata={"run_id": run_id, "thread_id": thread_id},
        )
        client_token = _active_client.set(client)
    except Exception:
        # This outer fallback only applies when constructing/closing telemetry fails.
        # The graph call remains the caller's responsibility and is never retried here.
        logger.exception("Langfuse request wrapper failed; continuing without export")
        yield None, []
        return
    try:
        yield observation, [handler]
    except BaseException as exc:
        _active_client.reset(client_token)
        for scope in (attrs_scope, observation_scope):
            try:
                scope.__exit__(type(exc), exc, exc.__traceback__)
            except Exception:
                logger.warning("Langfuse scope close failed; preserving graph exception", exc_info=True)
        raise
    else:
        _active_client.reset(client_token)
        for scope in (attrs_scope, observation_scope):
            try:
                scope.__exit__(None, None, None)
            except Exception:
                logger.warning("Langfuse scope close failed; preserving successful graph result", exc_info=True)


@contextmanager
def graph_node_observation(name: str, *, intent: str | None = None) -> Iterator[Any | None]:
    """Nest one low-data LangGraph node span under the request trace, when enabled."""
    client = _active_client.get()
    if client is None:
        yield None
        return
    try:
        scope = client.start_as_current_observation(
            as_type="span", name=f"graph.{name}",
            input={"node": name, "intent": intent or "unknown"},
        )
        span = scope.__enter__()
    except Exception:
        logger.warning("Langfuse node span unavailable; continuing", exc_info=True)
        yield None
        return
    try:
        yield span
    except BaseException as exc:
        try:
            scope.__exit__(type(exc), exc, exc.__traceback__)
        except Exception:
            logger.warning("Langfuse node span close failed", exc_info=True)
        raise
    else:
        try:
            scope.__exit__(None, None, None)
        except Exception:
            logger.warning("Langfuse node span close failed", exc_info=True)


def safe_score(settings: Any, *, trace_id: str, label: str) -> bool:
    """Send an enum-only user score after the caller verifies run ownership."""
    if not langfuse_status(settings)["enabled"]:
        return False
    try:
        from langfuse import get_client

        get_client().create_score(
            name="user-feedback", value=label, trace_id=trace_id,
            data_type="CATEGORICAL", score_id=f"{trace_id}-user-feedback",
        )
        return True
    except Exception:
        logger.exception("Langfuse feedback export failed")
        return False
