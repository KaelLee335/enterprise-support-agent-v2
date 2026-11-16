import json
import logging

from support_agent.observability import JsonFormatter, redact_user_input


def test_user_input_redaction_masks_credentials_and_contact_data():
    value = "email me@example.com or call 13812345678; api_key=sk-testsecret123456789"

    redacted = redact_user_input(value)

    assert "me@example.com" not in redacted
    assert "13812345678" not in redacted
    assert "sk-testsecret123456789" not in redacted
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted
    assert "[REDACTED]" in redacted


def test_json_formatter_emits_trace_duration_and_retrieval_summary():
    record = logging.LogRecord(
        name="agent", level=logging.INFO, pathname=__file__, lineno=1,
        msg="Agent node finished", args=(), exc_info=None,
    )
    record.event = "node_end"
    record.trace_id = "trace-123"
    record.duration_ms = 12.5
    record.evidence_ids = ["POL-06"]
    record.retrieved_sources = [{"source_id": "POL-06", "distance": 0.12}]

    output = json.loads(JsonFormatter().format(record))

    assert output["trace_id"] == "trace-123"
    assert output["duration_ms"] == 12.5
    assert output["evidence_ids"] == ["POL-06"]
    assert output["retrieved_sources"][0]["distance"] == 0.12
