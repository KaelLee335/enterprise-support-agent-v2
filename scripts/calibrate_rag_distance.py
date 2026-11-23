"""Measure exploratory distance separation for answerable vs. unsupported probes.

This is a calibration aid only. It does not modify the vector store, choose or
apply a production threshold, call the chat model, or change answer behavior.
Running it sends the synthetic probes below to the configured embedding API.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from support_agent.config import get_settings
from support_agent.rag.retrieval import create_siliconflow_embeddings, open_configured_policy_store


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data" / "evaluation" / "oos" / "embedding_distance_calibration_v1.md"
TOP_K = 4

# Synthetic questions grounded in the fictional policy corpus. These are new
# calibration probes, not copies of the 45 development cases or the 15 OOS set.
PROBES = [
    {"id": "IN-01", "kind": "answerable", "target": "POL-01", "question": "我是在你们演示商城买的键盘，这个售后规则适用吗？"},
    {"id": "IN-02", "kind": "answerable", "target": "POL-02", "question": "刚签收几天，包装配件都在，只是觉得不合适，能退吗？"},
    {"id": "IN-03", "kind": "answerable", "target": "POL-03", "question": "鼠标有质量问题，收货两周内可以换新吗？"},
    {"id": "IN-04", "kind": "answerable", "target": "POL-04", "question": "键盘进了水还能走免费保修吗？"},
    {"id": "IN-05", "kind": "answerable", "target": "POL-05", "question": "质量问题确认以后，退回去的邮费谁出？"},
    {"id": "IN-06", "kind": "answerable", "target": "POL-06", "question": "商家显示退款中，什么时候银行卡能看到钱？"},
    {"id": "IN-07", "kind": "answerable", "target": "POL-07", "question": "显示已经发货了，大概几天能送到？"},
    {"id": "IN-08", "kind": "answerable", "target": "POL-08", "question": "订单号格式是什么？可以一次查好几个吗？"},
    {"id": "IN-09", "kind": "answerable", "target": "POL-09", "question": "电子发票需要把抬头和税号发给机器人吗？"},
    {"id": "IN-10", "kind": "answerable", "target": "POL-10", "question": "政策里没写的情况应该怎么处理？"},
    {"id": "IN-11", "kind": "answerable", "target": "QUA-01", "question": "定制商品签收后发现质量瑕疵，提交申请要准备什么？"},
    {"id": "IN-12", "kind": "answerable", "target": "RET-01", "question": "定制商品不喜欢的话能不能七天无理由退？"},
    {"id": "OUT-01", "kind": "unsupported", "target": None, "question": "你们会员积分什么时候过期，能兑换什么礼品？"},
    {"id": "OUT-02", "kind": "unsupported", "target": None, "question": "能帮我把购物车里的商品改成分期付款吗？"},
    {"id": "OUT-03", "kind": "unsupported", "target": None, "question": "这个店铺的优惠券可以和员工折扣一起使用吗？"},
    {"id": "OUT-04", "kind": "unsupported", "target": None, "question": "你们办公桌的安装师傅周末会上门吗？"},
    {"id": "OUT-05", "kind": "unsupported", "target": None, "question": "海外买的显示器坏了，保修能寄到哪个国家维修？"},
    {"id": "OUT-06", "kind": "unsupported", "target": None, "question": "能不能把发票金额改高一点方便报销？"},
    {"id": "OUT-07", "kind": "unsupported", "target": None, "question": "你们门店周末几点营业，地址在哪里？"},
    {"id": "OUT-08", "kind": "unsupported", "target": None, "question": "购买办公设备可以开增值税专用发票吗？"},
    {"id": "OUT-09", "kind": "unsupported", "target": None, "question": "能帮我开一张采购订单并同步到公司的ERP系统吗？"},
    {"id": "OUT-10", "kind": "unsupported", "target": None, "question": "你们有没有以旧换新补贴，旧键盘能抵多少钱？"},
    {"id": "OUT-11", "kind": "unsupported", "target": None, "question": "能不能保证今天下单明天上午十点前送到？"},
    {"id": "OUT-12", "kind": "unsupported", "target": None, "question": "换货之后的新商品序列号在哪里查询？"},
]


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.4f}"


def _stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "p25": None, "median": None, "p75": None, "max": None}
    ordered = sorted(values)

    def percentile(fraction: float) -> float:
        position = (len(ordered) - 1) * fraction
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    return {
        "min": ordered[0],
        "p25": percentile(0.25),
        "median": percentile(0.5),
        "p75": percentile(0.75),
        "max": ordered[-1],
    }


def main() -> None:
    settings = get_settings()
    embeddings = create_siliconflow_embeddings(settings)
    store = open_configured_policy_store(settings=settings)
    collection_count = store._collection.count()
    if collection_count < 1:
        raise RuntimeError("Configured policy vector collection is empty")

    vectors = embeddings.embed_documents([probe["question"] for probe in PROBES])
    if len(vectors) != len(PROBES):
        raise RuntimeError("Embedding API returned a different number of vectors")

    records: list[dict] = []
    for probe, vector in zip(PROBES, vectors):
        matches = store.similarity_search_by_vector_with_relevance_scores(
            vector, k=collection_count
        )
        ranked = [
            {
                "source_id": str(doc.metadata.get("source_id", "unknown")),
                "title": str(doc.metadata.get("title", "")),
                "distance": float(distance),
            }
            for doc, distance in matches
        ]
        target_rank = next(
            (index for index, item in enumerate(ranked, start=1)
             if item["source_id"] == probe["target"]),
            None,
        ) if probe["target"] else None
        target_distance = ranked[target_rank - 1]["distance"] if target_rank else None
        records.append({
            **probe,
            "nearest_distance": ranked[0]["distance"] if ranked else None,
            "target_rank": target_rank,
            "target_distance": target_distance,
            "target_in_top4": target_rank is not None and target_rank <= TOP_K,
            "ranked_results": ranked,
        })

    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[record["kind"]].append(record)
    positive_nearest = [r["nearest_distance"] for r in groups["answerable"]]
    unsupported_nearest = [r["nearest_distance"] for r in groups["unsupported"]]
    target_distances = [r["target_distance"] for r in groups["answerable"] if r["target_distance"] is not None]
    top4_count = sum(r["target_in_top4"] for r in groups["answerable"])
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# RAG Embedding Distance Calibration (Exploratory)",
        "",
        f"- Generated: {generated_at}",
        f"- Embedding model: `{settings.siliconflow_embedding_model}`",
        f"- Vector collection: `{store._collection.name}` ({collection_count} chunks)",
        f"- Retrieval setting under review: Top-K={TOP_K}; all collection distances recorded for ranking analysis",
        f"- Probe set: {len(groups['answerable'])} answerable probes + {len(groups['unsupported'])} unsupported probes, all synthetic and fictional",
        "- Scope: embedding API only; no chat model call; no vector-store/database writes; no answer behavior change.",
        "- Distance meaning: raw Chroma distance from the existing store's configured metric; smaller is closer. It is not a probability.",
        "",
        "## Summary",
        "",
        f"- Target document appeared in Top-4 for {top4_count}/{len(groups['answerable'])} answerable probes ({top4_count / len(groups['answerable']):.1%}).",
        f"- Answerable target-document distance: min/median/max = {_fmt(min(target_distances) if target_distances else None)} / {_fmt(_stats(target_distances)['median'])} / {_fmt(max(target_distances) if target_distances else None)}.",
        f"- Answerable nearest-document distance: min/median/max = {_fmt(min(positive_nearest) if positive_nearest else None)} / {_fmt(_stats(positive_nearest)['median'])} / {_fmt(max(positive_nearest) if positive_nearest else None)}.",
        f"- Unsupported nearest-document distance: min/median/max = {_fmt(min(unsupported_nearest) if unsupported_nearest else None)} / {_fmt(_stats(unsupported_nearest)['median'])} / {_fmt(max(unsupported_nearest) if unsupported_nearest else None)}.",
        "",
        "### Distribution details",
        "",
        "| Probe group / distance | Min | P25 | Median | P75 | Max |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, values in (
        ("Answerable: target document", target_distances),
        ("Answerable: nearest document", positive_nearest),
        ("Unsupported: nearest document", unsupported_nearest),
    ):
        stats = _stats(values)
        lines.append(
            f"| {label} | {_fmt(stats['min'])} | {_fmt(stats['p25'])} | {_fmt(stats['median'])} | {_fmt(stats['p75'])} | {_fmt(stats['max'])} |"
        )
    lines.extend([
        "",
        "## Probe results",
        "",
        "| ID | Group | Expected document | Expected rank | Expected distance | Nearest distance | Top-4 | Retrieved order (all chunks) | Question |",
        "|---|---|---|---:|---:|---:|:---:|---|---|",
    ])
    for record in records:
        order = " → ".join(item["source_id"] for item in record["ranked_results"])
        lines.append(
            f"| {record['id']} | {record['kind']} | {record['target'] or 'none'} | {record['target_rank'] or '—'} | {_fmt(record['target_distance'])} | {_fmt(record['nearest_distance'])} | {'yes' if record['target_in_top4'] else 'no'} | {order} | {record['question']} |"
        )
    lines.extend([
        "",
        "## Interpretation and limits",
        "",
        "- These probes are a small, deliberately constructed calibration sample. They are not the 45-case development set or the 15-case OOS evaluation set, and they do not establish a generalizable cutoff.",
        "- Unsupported questions may still be close to generic fallback policies such as POL-10. Distance alone cannot determine whether a question is answerable; a single threshold can reject supported paraphrases or admit unsupported questions when the distributions overlap.",
        "- The results support deciding whether a candidate threshold deserves a larger labeled test, not applying one. No threshold is recommended for production/demo behavior from this report alone.",
        "- Synthetic questions and policy text were sent to the already-configured SiliconFlow Embedding endpoint. No real customer information was included.",
        "",
    ])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"Embedding probes: {len(PROBES)}; collection chunks: {collection_count}")
    print(f"Answerable target in Top-{TOP_K}: {top4_count}/{len(groups['answerable'])}")
    print(f"Answerable nearest median: {_fmt(_stats(positive_nearest)['median'])}")
    print(f"Unsupported nearest median: {_fmt(_stats(unsupported_nearest)['median'])}")


if __name__ == "__main__":
    main()
