from types import SimpleNamespace
from langfuse import OtelSpanIdentifier

from support_agent.langfuse_observability import (
    build_handler,
    langfuse_status,
    redact_text,
    safe_score,
    mask_export_batch,
    request_observation,
)


def test_langfuse_disabled_by_default_and_safe_score_is_noop():
    settings = SimpleNamespace(
        langfuse_enabled=False, langfuse_public_key=None,
        langfuse_secret_key=None, langfuse_base_url=None,
    )
    assert langfuse_status(settings) == {
        "enabled": False, "requested": False, "configured": False,
        "base_url": None, "reason": "disabled",
    }
    assert build_handler(settings) is None
    assert safe_score(settings, trace_id="trace", label="helpful") is False


def test_langfuse_status_never_exposes_credentials():
    settings = SimpleNamespace(
        langfuse_enabled=True, langfuse_public_key="pk-private",
        langfuse_secret_key="sk-private", langfuse_base_url="https://example.invalid",
    )
    state = langfuse_status(settings)
    assert state["enabled"] is True
    assert state["reason"] == "ready"
    assert "pk-private" not in repr(state) and "sk-private" not in repr(state)


def test_langfuse_text_redaction_masks_credentials_and_contact_data():
    value = "Bearer abc.def user@example.com 13812345678 sk-abcdefghijklmnop"
    result = redact_text(value)
    assert "abc.def" not in result
    assert "user@example.com" not in result
    assert "13812345678" not in result
    assert "sk-abcdefghijklmnop" not in result


def test_export_mask_removes_raw_prompt_and_redacts_remaining_pii():
    span_id = OtelSpanIdentifier(trace_id="0" * 32, span_id="1" * 16)
    span = SimpleNamespace(attributes={
        "langfuse.observation.input": "订单 1001，用户 user@example.com",
        "http.url": "https://example.invalid/user@example.com",
        "gen_ai.request.model": "Qwen/Qwen2.5-7B-Instruct",
    })
    result = mask_export_batch(params=SimpleNamespace(spans={span_id: span}))
    patch = result.span_patches[span_id]
    assert patch.set_attributes["langfuse.observation.input"] == "[REDACTED]"
    assert "user@example.com" not in patch.set_attributes["http.url"]
    assert "gen_ai.request.model" not in patch.set_attributes


def test_langfuse_sdk_initialization_failure_fails_open(monkeypatch):
    import support_agent.langfuse_observability as integration

    settings = SimpleNamespace(
        langfuse_enabled=True, langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test", langfuse_base_url="https://unused.invalid",
    )

    def unavailable(_settings):
        raise RuntimeError("simulated SDK initialization failure")

    monkeypatch.setattr(integration, "_configure_langfuse_client", unavailable)
    assert integration.build_handler(settings) is None
    with request_observation(
        settings, trace_id="a" * 32, thread_id="thread-demo", run_id="run-demo", user_scope="hashed-user",
    ) as (observation, callbacks):
        assert observation is None and callbacks == []
