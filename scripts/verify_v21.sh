#!/usr/bin/env bash
# Verify V2.1 MockShop business flow against the running WSL Compose stack.
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8000}"
python3 - "$BASE" <<'PY'
import hashlib
import hmac
import json
import os
import sys
import urllib.parse
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

base = sys.argv[1].rstrip("/")
webhook_secret = os.environ.get("MOCK_SHOP_WEBHOOK_SECRET", "demo-shop-webhook-secret")

def request(path, *, token=None, method="GET", body=None, signature=True):
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    if path == "/webhooks/mock-shop" and data is not None and signature:
        digest = hmac.new(webhook_secret.encode(), data, hashlib.sha256).hexdigest()
        headers["X-MockShop-Signature"] = f"sha256={digest}"
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {}
        return exc.code, parsed

def check(label, actual, expected):
    if actual != expected:
        raise SystemExit(f"FAIL {label}: expected {expected}, got {actual}")
    print(f"PASS {label}")

status, _ = request("/health")
check("health", status, 200)

status, order_a = request("/ecommerce/orders/2003", token="demo-a-local-token")
check("shop A can read own order", status, 200)
check("shop A order mapping", order_a.get("tenant_id"), "demo-a")
status, _ = request("/ecommerce/orders/2006", token="demo-a-local-token")
check("shop A cannot read shop B order", status, 404)
status, order_b = request("/ecommerce/orders/2006", token="demo-b-local-token")
check("shop B can read own order", status, 200)
check("shop B order mapping", order_b.get("tenant_id"), "demo-b")

reason = "演示质量问题"
status, eligibility = request(
    f"/ecommerce/orders/2003/aftersale-eligibility?reason={urllib.parse.quote(reason)}",
    token="demo-a-local-token",
)
check("aftersale eligibility API", status, 200)
if eligibility.get("eligible") is True:
    print("PASS fixture eligibility")
elif eligibility.get("reason_code") == "ALREADY_IN_AFTERSALE":
    print("PASS fixture eligibility (existing demo aftersale is expected on reruns)")
else:
    raise SystemExit(
        "FAIL fixture eligibility: expected eligible or ALREADY_IN_AFTERSALE, "
        f"got {eligibility.get('reason_code')}"
    )

application = {
    "reason": reason,
    "idempotency_key": "v21-wsl-verifier-demo-2003",
    "confirmed": True,
}
status, created = request(
    "/ecommerce/orders/2003/aftersales", token="demo-a-local-token",
    method="POST", body=application,
)
check("explicit demo aftersale request", status, 200)
check("application remains pending demo", created.get("status"), "pending_demo")
status, repeated = request(
    "/ecommerce/orders/2003/aftersales", token="demo-a-local-token",
    method="POST", body=application,
)
check("idempotent request retry", status, 200)
check("same application returned", repeated.get("request_id"), created.get("request_id"))

event_id = f"v21-wsl-verifier-event-2003-{uuid.uuid4().hex}"
event = {
    "event_id": event_id,
    "event_type": "order.shipped",
    "shop_id": "shop-demo-a",
    "order_id": "2003",
    "customer_id": "customer-demo-a",
    "platform_status": "WAIT_BUYER_RECEIVE",
    "occurred_at": datetime.now(timezone.utc).isoformat(),
}
status, receipt = request("/webhooks/mock-shop", method="POST", body=event)
check("signed webhook accepted", status, 200)
check("webhook initial event", receipt.get("duplicate"), False)
status, duplicate = request("/webhooks/mock-shop", method="POST", body=event)
check("duplicate webhook accepted", status, 200)
check("duplicate event is idempotent", duplicate.get("duplicate"), True)
status, synced = request("/ecommerce/orders/2003", token="demo-a-local-token")
check("webhook state visible to owner", synced.get("status"), "shipped")
status, _ = request("/webhooks/mock-shop", method="POST", body={**event, "event_id": f"invalid-{uuid.uuid4().hex}"}, signature=False)
check("invalid webhook signature rejected", status, 401)
status, _ = request(f"/webhooks/mock-shop/events/{event_id}", token="demo-b-local-token")
check("webhook event hidden across tenants", status, 404)
status, event_record = request(f"/webhooks/mock-shop/events/{event_id}", token="demo-a-local-token")
check("webhook event readable by owner", status, 200)
check("webhook event identity", event_record.get("event_id"), event_id)

print("All V2.1 checks passed.")
PY
