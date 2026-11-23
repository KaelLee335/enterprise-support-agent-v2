import json
import pytest

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from tests.oos import runner
from tests.test_rag import KeywordEmbeddings, policy_chunks
from support_agent.rag.index import index_policy_documents
from support_agent.rag.answer import answer_policy_question


def test_oos_retrieval_scoring_macro_components():
    assert runner.score_retrieval(["POL-02", "POL-03"], ["POL-03", "POL-04"]) == (True, 0.5)
    assert runner.score_retrieval([], ["POL-01"]) == (None, None)
    assert runner._unsupported_citation_labels("根据规则 [POL-02] [POL-05_SHIPPING_GUIDANCE]", ["POL-02"]) == ["POL-05_SHIPPING_GUIDANCE"]
    assert runner._check_fact("3至5", "发货后通常 3 至 5 个自然日送达")


def test_oos_screen_catches_contradictory_over_abstention():
    case = {
        "case_id": "HOLDOUT-07",
        "expected_behavior": "answer_business_day_definition",
        "relevant_document_ids": ["POL-06"],
    }
    answer = "无法从当前资料确认节假日是否计入；但工作日不含法定节假日。"

    failure_type, reason, _ = runner.classify_failure(case, ["POL-06"], answer)

    assert failure_type == "GENERATION"
    assert "先拒答" in reason


def test_oos_run_uses_only_supplied_cases_and_returns_answer_evidence(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "oos-index", KeywordEmbeddings())
    dataset = {"dataset_id": "test-oos", "evaluation_note": "test independence note", "cases": [{
        "case_id": "OOS-TEST", "question": "定制商品质量问题如何申请？",
        "expected_answer": "凭证并人工审核", "relevant_document_ids": ["QUA-01"],
        "expected_behavior": "answer_with_policy", "category": "test",
        "answer_checks": ["凭证", "人工审核"],
    }]}
    chat = FakeListChatModel(responses=["定制商品可提交质量售后申请，需要凭证并由人工审核。[QUA-01]"])
    progress = []
    results, metadata = runner.run(
        dataset, store=store, chat_model=chat, top_k=4, progress=progress.append
    )
    assert len(results) == 1
    assert results[0]["hit_at_4"] is True
    assert results[0]["answer_rule_pass"] is True
    assert results[0]["unsupported_citation_labels"] == []
    assert metadata["top_k"] == 4
    assert progress == ["OOS-TEST"]
    results[0]["failure_type"] = "GENERATION"
    results[0]["retrieved_documents"] = [{"source_id": "QUA-01", "title": "定制商品质量售后"}]
    report = runner.render_report(dataset, results, {**metadata, "embedding_model": "mock", "chat_model": "mock"})
    assert "与45条开发集分开" in report
    assert "test independence note" in report
    assert "QUA-01（定制商品质量售后）" in report
    assert "Hit@4" in report


def test_bad_case_ledger_separates_screening_from_human_root_cause():
    case = {
        "case_id": "OOS-TEST", "category": "combined_conditions",
        "question": "质量问题可以退货吗？", "expected_answer": "需人工核验。",
        "expected_behavior": "answer_with_policy", "relevant_document_ids": ["POL-02"],
    }
    dataset = {"dataset_id": "test-oos", "cases": [case]}
    result = {
        "case": case,
        "answer": "可以直接退货。",
        "retrieved_document_ids": ["POL-02"],
        "retrieved_documents": [{"source_id": "POL-02", "title": "退货政策", "distance": 0.2}],
        "unsupported_citation_labels": [],
        "failure_type": "GENERATION",
        "failure_reason": "规则要点未命中",
        "recommendation": "人工对照政策核查",
        "hit_at_4": True, "recall_at_4": 1.0,
        "answer_rule_pass": False, "abstention_rule_pass": None,
    }
    metadata = {
        "evaluated_at": "2026-11-22T00:00:00+00:00",
        "embedding_model": "mock", "chat_model": "mock", "top_k": 4,
    }

    ledger = runner.build_bad_case_records(dataset, [result], metadata)
    item = ledger["bad_cases"][0]

    assert ledger["schema_version"] == "1.0"
    assert item["expected_answer"] == "需人工核验。"
    assert item["actual_answer"] == "可以直接退货。"
    assert item["retrieved_documents"][0]["source_id"] == "POL-02"
    assert item["screening"]["is_root_cause"] is False
    assert item["root_cause_review"] == {
        "status": "pending", "category": None, "reviewer": None,
        "reviewed_at": None, "notes": None,
    }
    assert item["remediation"]["status"] == "not_started"
    assert "待复核假设" in runner.render_report(dataset, [result], metadata)


def test_bad_case_ledger_rejects_unknown_screening_category():
    case = {"case_id": "OOS-TEST", "category": "test", "question": "Q", "expected_answer": "A"}
    with pytest.raises(ValueError, match="unsupported Bad Case category"):
        runner.build_bad_case_records(
            {"dataset_id": "test", "cases": [case]},
            [{"case": case, "failure_type": "UNCLASSIFIED"}],
            {"evaluated_at": "now"},
        )


def test_answer_archive_keeps_passed_cases_and_supporting_evidence():
    case = {
        "case_id": "HOLDOUT-TEST", "category": "test",
        "question": "退货运费谁承担？", "expected_answer": "按政策处理。",
        "expected_behavior": "answer_with_policy", "relevant_document_ids": ["POL-05"],
    }
    dataset = {"dataset_id": "test-oos", "cases": [case]}
    result = {
        "case": case, "answer": "经确认后标准寄回运费由企业承担。[POL-05]",
        "retrieved_document_ids": ["POL-05"],
        "retrieved_documents": [{"source_id": "POL-05", "title": "运费", "distance": 0.1}],
        "hit_at_4": True, "recall_at_4": 1.0,
        "answer_rule_pass": True, "abstention_rule_pass": None,
        "unsupported_citation_labels": [], "failure_type": "",
        "failure_reason": "", "recommendation": "",
    }
    metadata = {
        "evaluated_at": "2026-11-23T12:00:00+00:00",
        "embedding_model": "mock-embedding", "chat_model": "mock-chat", "top_k": 4,
    }

    archive = runner.build_answer_records(dataset, [result], metadata)
    record = archive["records"][0]

    assert archive["dataset_id"] == "test-oos"
    assert archive["top_k"] == 4
    assert record["actual_answer"] == result["answer"]
    assert record["retrieved_documents"] == result["retrieved_documents"]
    assert record["screening_failure_type"] is None
    holdout_path = runner.PROJECT_ROOT / "data/evaluation/oos/rag_oos_v2_holdout.json"
    assert runner.answer_output_path(holdout_path).name == "rag_oos_v2_holdout_answers.json"


def test_oos_dataset_has_unique_cases_and_required_fields():
    dataset = json.loads(runner.DATASET.read_text(encoding="utf-8"))
    original = json.loads((runner.PROJECT_ROOT / "data/evaluation/v1_eval_cases.json").read_text(encoding="utf-8"))
    original_queries = {case["query"] for case in original["cases"]}
    assert len(dataset["cases"]) == 15
    assert not ({case["question"] for case in dataset["cases"]} & original_queries)
    assert all({"case_id", "question", "expected_answer", "relevant_document_ids", "expected_behavior", "category"} <= case.keys() for case in dataset["cases"])


def test_oos_v2_holdout_is_separate_and_has_dataset_specific_outputs():
    holdout_path = runner.PROJECT_ROOT / "data/evaluation/oos/rag_oos_v2_holdout.json"
    holdout = json.loads(holdout_path.read_text(encoding="utf-8"))
    v1 = json.loads(runner.DATASET.read_text(encoding="utf-8"))
    dev = json.loads((runner.PROJECT_ROOT / "data/evaluation/v1_eval_cases.json").read_text(encoding="utf-8"))
    prior_questions = {case["question"] for case in v1["cases"]}
    prior_questions |= {case["query"] for case in dev["cases"] if case.get("query")}

    assert holdout["status"] == "approved_for_evaluation"
    assert len(holdout["cases"]) == 15
    assert len({case["case_id"] for case in holdout["cases"]}) == 15
    assert not ({case["question"] for case in holdout["cases"]} & prior_questions)
    assert all(case["relevant_document_ids"] for case in holdout["cases"])
    report_path, bad_case_path = runner.output_paths(holdout_path)
    assert report_path.name == "rag_oos_v2_holdout_report.md"
    assert bad_case_path.name == "rag_oos_v2_holdout_bad_cases.json"
    assert runner.answer_output_path(holdout_path).name == "rag_oos_v2_holdout_answers.json"


def test_oos_report_independence_note_is_dataset_specific():
    dataset = {
        "dataset_id": "approved-holdout",
        "evaluation_note": "审核通过的独立样本外集；首次运行前未用于调优。",
        "cases": [],
    }
    report = runner.render_report(dataset, [], {
        "evaluated_at": "2026-11-23T00:00:00+00:00",
        "embedding_model": "mock", "chat_model": "mock", "top_k": 4,
    })
    assert "首次运行前未用于调优" in report
    assert "OOS-05" not in report
