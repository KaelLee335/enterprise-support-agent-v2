# -*- coding: utf-8 -*-
"""列出硅基流动免费聊天模型并实测一个。"""
import json
import os
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


def api(path):
    req = urllib.request.Request(
        BASE + path, headers={"Authorization": "Bearer " + KEY}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


data = api("/models")
ids = [m["id"] for m in data.get("data", [])]

# 硅基流动免费模型通常是特定小模型；按已知免费名单过滤
known_free = [
    i for i in ids
    if i in {
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen3-8B",
        "THUDM/glm-4-9b-chat",
        "THUDM/glm-4-9b-chat-0414",
        "Qwen/Qwen2.5-14B-Instruct",
        "deepseek-ai/DeepSeek-V2.5",
        "Qwen/Qwen3-14B",
        "Qwen/Qwen3-30B-A3B",
        "Qwen/Qwen3-32B",
        "moonshotai/Kimi-K2-Instruct",
        "zai-org/GLM-4.5-Air",
        "zai-org/GLM-4.6-Air-FP8",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        "Qwen/Qwen2.5-Coder-7B-Instruct",
        "TeleAI/TeleChat2-3B",
        "internlm/internlm2_5-7b-chat",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
    }
]
print("=== chat candidates (known free tier) ===")
for i in known_free:
    print(" ", i)

print("\n=== all ids containing keywords ===")
for i in sorted(ids):
    if any(k in i.lower() for k in ("qwen3", "glm", "deepseek", "kimi")):
        print(" ", i)

# 实测第一个候选（若为空则取 Qwen3-8B）
target = known_free[0] if known_free else "Qwen/Qwen3-8B"
print("\n=== test chat:", target, "===")
body = json.dumps({
    "model": target,
    "messages": [
        {"role": "user", "content": "只回答一个词：1+1等于几？"}
    ],
    "max_tokens": 512,
}).encode()
req = urllib.request.Request(
    BASE + "/chat/completions",
    data=body,
    headers={
        "Authorization": "Bearer " + KEY,
        "Content-Type": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=60) as r:
    out = json.load(r)
choice = out["choices"][0]
print("content:", choice["message"]["content"][:120])
print("finish_reason:", choice.get("finish_reason"))
print("usage:", out.get("usage"))
