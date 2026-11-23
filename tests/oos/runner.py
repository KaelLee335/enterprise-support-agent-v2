"""Independent retrieval and generation runner for the curated OOS set."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
from typing import Any

from support_agent.config import PROJECT_ROOT, get_settings
from support_agent.rag.answer import (
    answer_policy_question,
    create_siliconflow_chat_model,
)
from support_agent.rag.retrieval import (
    open_configured_policy_store,
)

DATASET = PROJECT_ROOT / "data/evaluation/oos/rag_oos_v1.json"
REPORT = PROJECT_ROOT / "data/evaluation/oos/rag_oos_v1_report.md"
BAD_CASE_REPORT = PROJECT_ROOT / "data/evaluation/oos/rag_oos_v1_bad_cases.json"
BAD_CASE_TAXONOMY = {
    "DATA", "CHUNK", "RETRIEVAL", "GENERATION", "BUSINESS", "ABSTENTION",
}


def score_retrieval(expected: list[str], retrieved: list[str]) -> tuple[bool | None, float | None]:
    if not expected:
        return None, None
    relevant = set(expected)
    found = relevant.intersection(retrieved)
    return bool(found), len(found) / len(relevant)


def _passes_abstention_check(answer: str, expected_behavior: str) -> bool:
    phrases = ["无法确认", "无法从", "不在", "原销售渠道", "没有规定", "未规定", "未明确"]
    equivalents = {
        "abstain_from_unapproved_outcome": ["不能承诺", "不等于批准", "无法直接", "需人工协商"],
        "abstain_from_free_warranty_promise": ["不在免费保修范围", "不能承诺免费", "需检测后确认"],
        "abstain_from_unspecified_evidence_format": ["没有规定", "未规定", "没有限定", "需人工确认材料"],
        "abstain_from_unspecified_reimbursement_limit": ["没有固定报销上限", "凭据由人工确认"],
        "abstain_from_real_time_tracking_claim": ["无法查询", "不能提供实时轨迹", "联系人工核查"],
        "abstain_from_unspecified_invoice_amount": ["金额调整规则", "无法确认", "人工核验"],
        "abstain_from_invoice_amount_adjustment": ["金额调整规则", "无法确认", "人工核验"],
        "refuse_fake_handoff": ["无法直接为您留", "不能代为", "没有真实工单"],
    }
    phrases.extend(equivalents.get(expected_behavior, []))
    if expected_behavior.startswith("abstain"):
        phrases.extend(["无法承诺", "不能承诺", "不承诺", "需检测后确认", "不能直接", "无法直接"])
    return any(phrase in answer for phrase in phrases)


def classify_failure(case: dict[str, Any], retrieved: list[str], answer: str) -> tuple[str, str, str]:
    expected_ids = set(case["relevant_document_ids"])
    if not expected_ids:
        if case["expected_behavior"].startswith(("abstain", "scope_")) and not _passes_abstention_check(
            answer, case["expected_behavior"]
        ):
            return "ABSTENTION", "无答案/范围外问题未明确拒答", "人工核对拒答边界与 POL-01/POL-10 覆盖。"
        return "", "", ""
    if not expected_ids.intersection(retrieved):
        return "RETRIEVAL", "Top-4 未包含标注相关来源", "先确认索引包含来源，再分析查询表达与向量召回。"
    if len(expected_ids.intersection(retrieved)) < len(expected_ids):
        return "RETRIEVAL", "Top-4 只召回部分标注来源", "检查多证据问题的候选排序与各来源覆盖。"
    if case["expected_behavior"] == "clarify_missing_facts" and not any(
        phrase in answer for phrase in ("请提供", "请告知", "麻烦补充", "签收日期", "哪天签收", "是否属于质量问题", "商品故障")
    ):
        return "ABSTENTION", "信息不足时未提出必要澄清问题", "确认业务是否要求先澄清，再调整路由/澄清规则并由人工复核。"
    if case["expected_behavior"] == "answer_business_day_definition" and any(
        phrase in answer for phrase in ("无法从当前资料确认", "无法确认法定节假日", "不确定法定节假日")
    ):
        return (
            "GENERATION",
            "对政策已明确的工作日定义先拒答，后续又给出相反的肯定结论",
            "优先直接引用 POL-06 的工作日定义，并测试拒答与肯定结论不自相矛盾。",
        )
    missing = [fact for fact in case.get("answer_checks", []) if not _check_fact(fact, answer)]
    if missing:
        labels = ["/".join(item) if isinstance(item, list) else item for item in missing]
        return "GENERATION", "检索来源齐全但规则要点检查未命中：" + "、".join(labels), "人工复核答案语义；不要据此自动改 Prompt。"
    return "", "", ""


def _check_fact(expected: str | list[str], answer: str) -> bool:
    options = expected if isinstance(expected, list) else [expected]
    normalized_answer = re.sub(r"\s+", "", answer)
    semantic_aliases = {
        "收货": ["商品寄回并经检验通过", "寄回商品并经检验通过", "收回商品并检验通过"],
        "人工协商": ["联系人工进行协商", "联系人工客服进行协商", "由人工协商处理"],
        "无法确认/需要检测": ["检测后确认", "需检测后确认", "检测后才能确认"],
        "无法确认": ["还不能判断", "不能据此判断", "需人工核实"],
        "需要检测": ["检测后确认", "需检测后确认", "要检测后确认"],
        "人工审核": ["由人工审核", "人工核验"],
        "人工核查": ["联系人工客服进行核查", "联系人工核实", "人工客服核查"],
        "不能修改": ["无法直接修改", "无法执行修改"],
        "人工": ["人工客服", "客服团队", "联系人工"],
        "不能代为提交/无法提交": ["仅在人工受理渠道提交", "仅通过人工受理渠道提交", "本聊天不收集"],
        "不能代为提交": ["仅在人工受理渠道提交", "仅通过人工受理渠道提交"],
        "不能代为留言/不能声称已留言/没有真实工单": ["无法直接为您留回电请求", "无法直接留回电请求", "不能为您留回电请求"],
        "不能代为留言": ["无法直接为您留回电请求", "无法直接留回电请求", "不能为您留回电请求"],
        "不能声称已留言": ["无法直接为您留回电请求", "无法直接留回电请求"],
        "没有真实工单": ["无法直接为您留回电请求", "无法直接留回电请求"],
        "没有规定/未规定": ["没有限定", "未明确规定", "当前资料没有规定"],
        "没有规定": ["没有限定", "未明确规定", "当前资料没有规定"],
        "没有固定": ["没有规定固定", "未设固定", "没有设定固定"],
        "不等于批准": ["不能承诺", "不代表已批准", "并非自动批准"],
        "不能保证送达": ["不承诺具体送达时间", "不承诺具体到货日"],
    }
    expanded_options = [
        alternative
        for option in options
        for alternative in [option, *semantic_aliases.get(option, [])]
    ]
    return any(re.sub(r"\s+", "", option) in normalized_answer for option in expanded_options)


def _unsupported_citation_labels(answer: str, retrieved: list[str]) -> list[str]:
    labels = re.findall(r"\[([A-Z][A-Z0-9_-]+)\]", answer)
    return list(dict.fromkeys(label for label in labels if label not in set(retrieved)))


def render_report(
    dataset: dict,
    results: list[dict],
    metadata: dict,
    *,
    answer_artifact: str | None = None,
) -> str:
    labeled = [r for r in results if r["hit_at_4"] is not None]
    no_answer = [r for r in results if r["case"]["expected_behavior"].startswith(("abstain", "scope_"))]
    answer_checked = [r for r in results if r["answer_rule_pass"] is not None]
    bad = [r for r in results if r["failure_type"]]
    hit = sum(r["hit_at_4"] for r in labeled) / len(labeled) if labeled else None
    recall = sum(r["recall_at_4"] for r in labeled) / len(labeled) if labeled else None
    answer_rate = sum(r["answer_rule_pass"] for r in answer_checked) / len(answer_checked) if answer_checked else None
    abstain_ok = sum(r["abstention_rule_pass"] for r in no_answer) / len(no_answer) if no_answer else None
    citation_clean = sum(not r["unsupported_citation_labels"] for r in results) / len(results) if results else None
    counts = Counter(r["failure_type"] for r in bad)
    lines = [
        "# RAG 样本外测试报告", "", f"- 数据集：`{dataset['dataset_id']}`（与45条开发集分开）",
        f"- 运行时间：{metadata['evaluated_at']}", f"- 案例：{len(results)}；分类：{dict(Counter(c['category'] for c in dataset['cases']))}",
        f"- 独立性说明：{dataset.get('evaluation_note', '该数据集用于独立评估；结果不可与原45条开发集混算。')}",
        f"- Embedding：{metadata['embedding_model']}；LLM：{metadata['chat_model']}；Top-K：{metadata['top_k']}",
        f"- 逐案例答复与检索证据：`{answer_artifact}`" if answer_artifact else "- 逐案例答复与检索证据：由执行器生成独立 JSON 附件。",
        "- 语义正确性由规则要点初筛并需人工审核；无 LLM judge。", "",
        "## 指标", "",
        f"- Hit@4：{hit:.1%}（{len(labeled)}条有相关文档标注案例；只要命中一个来源即算命中）" if hit is not None else "- Hit@4：N/A",
        f"- Macro Recall@4：{recall:.1%}（仅在有相关来源标注案例上逐题算召回再宏平均）" if recall is not None else "- Macro Recall@4：N/A",
        f"- 答案规则要点通过率：{answer_rate:.1%}（{len(answer_checked)}条；只是规则初筛，不等于语义正确率）" if answer_rate is not None else "- 答案规则要点通过率：N/A",
        f"- 无答案拒答规则通过率：{abstain_ok:.1%}（{len(no_answer)}条；人工仍需确认是否合理）" if abstain_ok is not None else "- 无答案拒答规则通过率：N/A",
        f"- 引用标签与本次检索来源匹配率：{citation_clean:.1%}（只检查方括号编号是否属于召回来源，不代表事实蕴含已验证）" if citation_clean is not None else "- 引用标签与本次检索来源匹配率：N/A",
        "- 原开发集历史指标：Hit@4 100%、Recall@4 86.6%（36条有标签案例）；与本报告不合并。", "",
        "## Bad Case 分类", "",
        "本节是自动规则初筛，标签和原因均为待复核假设，不代表已确认根因。",
        f"案例数：{len(bad)}；初筛分类计数：{dict(counts)}", "",
        "## 失败案例", ""
    ]
    if not bad:
        lines.append("本次规则初筛未发现 Bad Case；答案仍需人工审核。")
    for item in bad:
        case = item["case"]
        retrieved_titles = "; ".join(
            f"{doc['source_id']}（{doc['title']}）"
            for doc in item.get("retrieved_documents", [])
        ) or "无"
        lines.extend([
            f"### {case['case_id']} [{item['failure_type']}]", "",
            f"- 问题：{case['question']}", f"- 预期：{case['expected_answer']}",
            f"- 实际：{item['answer']}",
            f"- 检索来源：{', '.join(item['retrieved_document_ids']) or '无'}",
            f"- 检索文档：{retrieved_titles}",
            f"- 未匹配的引用标签：{', '.join(item['unsupported_citation_labels']) or '无'}",
            f"- 可能原因：{item['failure_reason']}", f"- 建议：{item['recommendation']}", ""
        ])
    lines.extend([
        "## 解释与后续", "",
        "自动初筛只描述观测到的失败表现。DATA、CHUNK、RETRIEVAL、GENERATION、BUSINESS、ABSTENTION 中的最终根因需人工对照知识库、权限和业务规则确认。",
        "每条失败的结构化记录写入本数据集对应的 Bad Case JSON；请填写 `root_cause_review`，并记录 `remediation` 与回归证据。",
        "",
    ])
    return "\n".join(lines)


def build_bad_case_records(dataset: dict, results: list[dict], metadata: dict) -> dict:
    """Build a machine-readable screening ledger without claiming root cause."""
    bad_cases = []
    for result in results:
        screening_type = result.get("failure_type")
        if not screening_type:
            continue
        if screening_type not in BAD_CASE_TAXONOMY:
            raise ValueError(f"unsupported Bad Case category: {screening_type}")
        case = result["case"]
        bad_cases.append({
            "case_id": case["case_id"],
            "case_category": case["category"],
            "question": case["question"],
            "expected_answer": case["expected_answer"],
            "actual_answer": result["answer"],
            "retrieved_document_ids": result["retrieved_document_ids"],
            "retrieved_documents": result["retrieved_documents"],
            "unsupported_citation_labels": result["unsupported_citation_labels"],
            "screening": {
                "category": screening_type,
                "reason": result["failure_reason"],
                "suggested_direction": result["recommendation"],
                "is_root_cause": False,
            },
            "root_cause_review": {
                "status": "pending",
                "category": None,
                "reviewer": None,
                "reviewed_at": None,
                "notes": None,
            },
            "remediation": {
                "status": "not_started",
                "summary": None,
                "code_or_data_refs": [],
                "regression_test": None,
                "verified_at": None,
            },
        })
    return {
        "schema_version": "1.0",
        "dataset_id": dataset["dataset_id"],
        "evaluated_at": metadata["evaluated_at"],
        "classification_note": "screening labels are hypotheses; only human-reviewed root_cause_review is an adjudicated cause",
        "allowed_root_cause_categories": sorted(BAD_CASE_TAXONOMY),
        "bad_cases": bad_cases,
    }


def build_answer_records(dataset: dict, results: list[dict], metadata: dict) -> dict:
    """Keep every generated answer and its evidence, including rule-screened passes."""
    return {
        "schema_version": "1.0",
        "dataset_id": dataset["dataset_id"],
        "evaluated_at": metadata["evaluated_at"],
        "embedding_model": metadata["embedding_model"],
        "chat_model": metadata["chat_model"],
        "top_k": metadata["top_k"],
        "records": [
            {
                "case_id": item["case"]["case_id"],
                "category": item["case"]["category"],
                "question": item["case"]["question"],
                "expected_answer": item["case"]["expected_answer"],
                "expected_behavior": item["case"]["expected_behavior"],
                "relevant_document_ids": item["case"]["relevant_document_ids"],
                "actual_answer": item["answer"],
                "retrieved_document_ids": item["retrieved_document_ids"],
                "retrieved_documents": item["retrieved_documents"],
                "hit_at_4": item["hit_at_4"],
                "recall_at_4": item["recall_at_4"],
                "answer_rule_pass": item["answer_rule_pass"],
                "abstention_rule_pass": item["abstention_rule_pass"],
                "unsupported_citation_labels": item["unsupported_citation_labels"],
                "screening_failure_type": item["failure_type"] or None,
                "screening_failure_reason": item["failure_reason"] or None,
            }
            for item in results
        ],
    }


def run(dataset: dict, *, store, chat_model, top_k: int = 4, progress=None) -> tuple[list[dict], dict]:
    results = []
    for case in dataset["cases"]:
        if progress is not None:
            progress(case["case_id"])
        answer_result = answer_policy_question(case["question"], store=store, chat_model=chat_model, top_k=top_k)
        evidence = answer_result.evidence
        ids = [item.source_id for item in evidence]
        hit, recall = score_retrieval(case["relevant_document_ids"], ids)
        checks = case.get("answer_checks", [])
        rule_pass = all(_check_fact(term, answer_result.answer) for term in checks) if checks else None
        abstention_pass = None
        if case["expected_behavior"].startswith(("abstain", "scope_")):
            abstention_pass = _passes_abstention_check(answer_result.answer, case["expected_behavior"])
        if case["expected_behavior"] == "clarify_missing_facts":
            abstention_pass = any(phrase in answer_result.answer for phrase in ("请提供", "请告知", "麻烦补充", "签收日期", "哪天签收", "是否属于质量问题", "商品故障"))
        failure_type, reason, recommendation = classify_failure(case, ids, answer_result.answer)
        unsupported_labels = _unsupported_citation_labels(answer_result.answer, ids)
        if unsupported_labels:
            citation_note = "答复含不属于本次召回来源的引用标签：" + ", ".join(unsupported_labels)
            if failure_type:
                reason += "；" + citation_note
            else:
                failure_type, reason, recommendation = "GENERATION", citation_note, "核对答复中的引用标记是否应映射到真实政策编号。"
        if rule_pass is False and not failure_type:
            failure_type, reason, recommendation = "BUSINESS", "回答未包含预期业务要点", "对照对应政策原文进行人工判断，不自动修改约束。"
        results.append({
            "case": case, "answer": answer_result.answer,
            "retrieved_document_ids": ids,
            "retrieved_documents": [{"source_id": e.source_id, "title": e.title, "distance": e.distance} for e in evidence],
            "hit_at_4": hit, "recall_at_4": recall,
            "answer_rule_pass": rule_pass, "abstention_rule_pass": abstention_pass,
            "unsupported_citation_labels": unsupported_labels,
            "failure_type": failure_type, "failure_reason": reason, "recommendation": recommendation,
        })
    return results, {"evaluated_at": datetime.now(timezone.utc).isoformat(), "top_k": top_k}


def output_paths(dataset_path: Path) -> tuple[Path, Path]:
    return (
        dataset_path.with_name(f"{dataset_path.stem}_report.md"),
        dataset_path.with_name(f"{dataset_path.stem}_bad_cases.json"),
    )


def answer_output_path(dataset_path: Path) -> Path:
    return dataset_path.with_name(f"{dataset_path.stem}_answers.json")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run an isolated RAG OOS evaluation dataset.")
    parser.add_argument(
        "--dataset", type=Path, default=DATASET,
        help="JSON dataset path (default: the OOS-v1 regression dataset)",
    )
    args = parser.parse_args(argv)
    dataset_path = args.dataset.resolve()
    report_path, bad_case_path = output_paths(dataset_path)
    answer_path = answer_output_path(dataset_path)
    settings = get_settings()
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    store = open_configured_policy_store(settings=settings)
    chat_model = create_siliconflow_chat_model(settings)
    results, run_meta = run(
        dataset,
        store=store,
        chat_model=chat_model,
        top_k=4,
        progress=lambda case_id: print(f"Evaluating {case_id}...", flush=True),
    )
    metadata = {**run_meta, "embedding_model": settings.siliconflow_embedding_model, "chat_model": settings.siliconflow_chat_model}
    report_path.write_text(
        render_report(dataset, results, metadata, answer_artifact=answer_path.name),
        encoding="utf-8",
    )
    ledger = build_bad_case_records(dataset, results, metadata)
    bad_case_path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    answer_records = build_answer_records(dataset, results, metadata)
    answer_path.write_text(
        json.dumps(answer_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OOS report: {report_path}")
    print(f"Bad Case ledger: {bad_case_path}")
    print(f"Per-case answers and evidence: {answer_path}")
    print(f"Cases: {len(results)}; report written for manual review.")


if __name__ == "__main__":
    main()
