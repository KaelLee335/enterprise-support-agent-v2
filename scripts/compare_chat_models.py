# -*- coding: utf-8 -*-
"""对比三个免费聊天模型在 RAG 场景下的表现。"""
import json
import os
import time
import urllib.request

BASE = "https://api.siliconflow.cn/v1"


def load_key():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("SILICONFLOW_API_KEY="):
                return line.strip().split("=", 1)[1]
    raise SystemExit("key not found")


KEY = load_key()


def chat(model, question, max_tokens=300):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as r:
        out = json.load(r)
    dt = time.time() - t0
    msg = out["choices"][0]["message"]
    usage = out["usage"]
    # 兼容思考模型：content 可能在 reasoning_content 之后
    reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
    return {
        "latency": round(dt, 1),
        "completion": usage["completion_tokens"],
        "reasoning": reasoning,
        "content": (msg.get("content") or "")[:200],
    }


Q = (
    "根据以下证据回答问题，并标注引用来源。若证据不足以回答，请直接说「证据不足」。\n\n"
    "证据[1]: 15天以内出现质量问题可申请质量换货，需上传现场照片。\n"
    "证据[2]: 退款发起后1-3个工作日审核，1-5个工作日到账。\n\n"
    "问题: 保修期内产品质量问题怎么申请售后？"
)

for m in ["Qwen/Qwen3-8B", "Qwen/Qwen2.5-7B-Instruct", "zai-org/GLM-4.5-Air"]:
    print("=" * 20, m)
    try:
        r = chat(m, Q)
        print(f"  latency={r['latency']}s completion={r['completion']}tok reasoning={r['reasoning']}tok")
        print("  content:", r["content"].replace("\n", " "))
    except Exception as e:
        print("  FAILED:", e)
