from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from support_agent.config import Settings
from support_agent.rag.index import index_policy_documents
from support_agent.rag.policies import load_policy_documents, split_policy_documents
from support_agent.rag.evaluation import evaluate_cases, score_retrieved_sources
from support_agent.rag.answer import answer_policy_question, generate_answer_from_evidence
from support_agent.rag.answer_constraints import apply_answer_constraints, match_answer_constraints
from langchain_chroma import Chroma
from support_agent.rag.retrieval import (
    RetrievedPolicy,
    create_siliconflow_embeddings,
    retrieve_policies,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class KeywordEmbeddings(Embeddings):
    """Small deterministic test embedder; it never calls a network API."""

    labels = ("质量", "退货", "退款", "定制")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(label in text) for label in self.labels]


def policy_chunks() -> list:
    documents = load_policy_documents(PROJECT_ROOT / "data" / "policies")
    return split_policy_documents(documents, chunk_size=400, chunk_overlap=0)


def test_policy_loader_preserves_one_source_per_current_chunk():
    chunks = policy_chunks()

    assert len(chunks) == 12
    assert {chunk.metadata["source_id"] for chunk in chunks} >= {"POL-02", "QUA-01", "RET-01"}
    assert all(chunk.metadata["source_id"] in chunk.metadata["chunk_id"] for chunk in chunks)
    assert next(chunk for chunk in chunks if chunk.metadata["source_id"] == "QUA-01").metadata[
        "source_version"
    ] == "V2"


def test_policy_index_upserts_only_changed_chunks_and_returns_evidence(tmp_path):
    chunks = policy_chunks()
    embeddings = KeywordEmbeddings()

    store, first_indexed = index_policy_documents(chunks, tmp_path / "chroma", embeddings)
    same_store, second_indexed = index_policy_documents(chunks, tmp_path / "chroma", embeddings)
    results = retrieve_policies("定制商品质量问题", store=same_store, top_k=4)

    assert first_indexed == 12
    assert second_indexed == 0
    assert len(results) == 4
    assert {result.source_id for result in results} & {"QUA-01", "POL-03"}
    assert all(result.content and result.title for result in results)


def test_empty_index_input_does_not_clear_existing_collection(tmp_path):
    with pytest.raises(ValueError, match="refusing to clear"):
        index_policy_documents([], tmp_path / "chroma", KeywordEmbeddings())


def test_retrieval_rejects_empty_queries(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())

    with pytest.raises(ValueError, match="query must not be empty"):
        retrieve_policies("  ", store=store)


def test_siliconflow_embedding_requires_local_api_key():
    settings = Settings(database_path=PROJECT_ROOT / "data" / "test.db")

    with pytest.raises(RuntimeError, match="SILICONFLOW_API_KEY is missing"):
        create_siliconflow_embeddings(settings)


def test_retrieval_evidence_scoring_counts_partial_recall():
    score = score_retrieved_sources(["POL-02", "POL-03"], ["POL-03", "POL-04"])

    assert score["hit"] is True
    assert score["recall"] == 0.5
    assert score["all_expected_found"] is False


def test_evaluation_ignores_cases_without_evidence_labels(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())
    cases = [
        {"id": "scored", "category": "qa", "query": "质量", "required_evidence": ["POL-03"]},
        {"id": "unscored", "category": "safe", "query": "修改地址", "required_evidence": []},
    ]

    records, summary = evaluate_cases(
        cases, store=store, embeddings=KeywordEmbeddings(), top_k=3
    )

    assert len(records) == 1
    assert summary["scored_cases"] == 1
    assert 0.0 <= summary["mean_recall_at_k"] <= 1.0


def test_rag_answer_checks_citations_against_retrieved_evidence(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())
    chat = FakeListChatModel(responses=["定制商品仍可提交质量售后申请，需提供凭证并由人工审核。[QUA-01]"])

    result = answer_policy_question(
        "定制商品有质量问题怎么办？", store=store, chat_model=chat, top_k=4
    )

    assert "[QUA-01]" in {f"[{citation}]" for citation in result.citations}
    assert result.citation_check_passed is True
    assert result.unknown_citations == []


def test_rag_answer_flags_citations_not_in_retrieved_evidence(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())
    chat = FakeListChatModel(responses=["可申请处理。[POL-09]"])

    result = answer_policy_question(
        "定制商品质量问题", store=store, chat_model=chat, top_k=1
    )

    assert result.citation_check_passed is False
    assert result.unknown_citations == ["POL-09"]


def test_rag_answer_does_not_call_model_when_retrieval_is_empty(tmp_path):
    store = Chroma(
        collection_name="empty_policy_test",
        embedding_function=KeywordEmbeddings(),
        persist_directory=str(tmp_path / "empty-chroma"),
    )
    chat = FakeListChatModel(responses=["should not be used"])

    result = answer_policy_question("陌生主题", store=store, chat_model=chat)

    assert result.evidence == []
    assert "无法确认" in result.answer


def test_ambiguous_return_eligibility_asks_for_decisive_facts(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "clarify-chroma", KeywordEmbeddings())
    result = answer_policy_question(
        "质量问题的键盘还能退货吗？",
        store=store,
        chat_model=FakeListChatModel(responses=[]),
        top_k=4,
    )

    assert "哪天签收" in result.answer
    assert "商品故障" in result.answer
    assert "配件和包装" in result.answer
    assert result.citation_check_passed is True
    assert result.citations == ["POL-02"]


def test_quality_shipping_constraint_does_not_add_irrelevant_no_reason_fee():
    evidence = [RetrievedPolicy("POL-05", "退换货运费", "quality shipping policy", 0.1)]
    constraints = match_answer_constraints("质量故障，寄回邮费谁出？", evidence)
    answer = "经人工确认的非人为质量问题，标准寄回运费由企业承担；请先联系人工获取退货指引。[POL-05]"

    result, enforced = apply_answer_constraints(answer, constraints)

    assert "无理由退货寄回运费由用户承担" not in result
    assert "POL-05_SHIPPING_AND_GUIDANCE" not in result
    assert enforced == []


def test_shipment_constraint_adds_missing_delivery_window_without_boilerplate():
    evidence = [RetrievedPolicy("POL-07", "发货与物流", "shipping and delivery window", 0.1)]
    constraints = match_answer_constraints("付款后两天还没发货，明天能到吗？", evidence)
    answer = "通常订单会在付款后2个工作日内发出，但不能保证明天送达。[POL-07]"

    result, enforced = apply_answer_constraints(answer, constraints)

    assert "发货后通常 3 至 5 个自然日送达" in result
    assert "不能保证明天送达" in result
    assert "\n\n" not in result
    assert result.count("[POL-07]") == 1
    assert enforced == ["POL07_SHIPMENT_WINDOW"]


def test_refund_workday_answer_directly_states_holiday_exclusion():
    evidence = [RetrievedPolicy(
        "POL-06", "退款进度", "工作日不含周末及法定节假日。", 0.1
    )]
    result = generate_answer_from_evidence(
        "如果退款处理期间遇到法定节假日，节假日也算在到账的工作日里吗？",
        evidence=evidence,
        chat_model=FakeListChatModel(responses=[]),
    )

    assert "工作日不含周末及法定节假日" in result.answer
    assert "无法从当前资料确认" not in result.answer
    assert result.citations == ["POL-06"]
    assert result.enforced_constraint_ids == ["POL06_WORKDAY_EXCLUDES_HOLIDAYS"]


@pytest.mark.parametrize(
    ("question", "evidence", "expected_phrase", "expected_citations"),
    [
        (
            "订单完成了，是不是就不能再申请符合政策的售后了？",
            [RetrievedPolicy("POL-08", "订单查询与权限", "completed-order rule", 0.1)],
            "订单流程结束",
            ["POL-08"],
        ),
        (
            "你们能承诺我这款扩展坞坏了多久修好吗？",
            [RetrievedPolicy("POL-04", "保修范围", "repair time requires inspection", 0.1)],
            "无法承诺具体周期",
            ["POL-04"],
        ),
        (
            "我在海外买的二手鼠标，支持国际保修吗？",
            [
                RetrievedPolicy("POL-01", "服务范围", "second hand excluded", 0.1),
                RetrievedPolicy("POL-10", "人工协助与未知问题", "unknown policy guidance", 0.2),
            ],
            "原销售渠道",
            ["POL-01", "POL-10"],
        ),
        (
            "我买的是第三方平台的二手鼠标，能按你们商城的保修政策免费修吗？",
            [
                RetrievedPolicy("POL-04", "保修范围", "warranty policy", 0.1),
                RetrievedPolicy("POL-01", "服务范围", "scope limitation", 0.2),
                RetrievedPolicy("POL-10", "人工协助与未知问题", "unknown policy guidance", 0.3),
            ],
            "不在本演示政策范围",
            ["POL-01", "POL-10"],
        ),
        (
            "键盘是定制配色，签收第4天发现按键坏了，能不能处理，邮费谁出？",
            [
                RetrievedPolicy("POL-03", "质量换货", "quality exchange", 0.1),
                RetrievedPolicy("POL-05", "退换货运费", "shipping", 0.2),
            ],
            "仍在15个自然日内",
            ["POL-03", "POL-05"],
        ),
        (
            "质量问题我想寄回去，先寄到付行不行？",
            [
                RetrievedPolicy("POL-03", "质量换货", "quality exchange", 0.1),
                RetrievedPolicy("POL-05", "退换货运费", "shipping", 0.2),
            ],
            "不要直接寄到付件",
            ["POL-05"],
        ),
    ],
)
def test_known_policy_edges_get_short_cited_answers(question, evidence, expected_phrase, expected_citations):
    result = generate_answer_from_evidence(
        question,
        evidence=evidence,
        chat_model=FakeListChatModel(responses=[]),
    )

    assert expected_phrase in result.answer
    assert result.citations == expected_citations
    assert result.citation_check_passed is True


@pytest.mark.parametrize(
    ("question", "evidence", "expected_phrase", "citation"),
    [
        (
            "我拆开鼠标自己换了微动，能按免费保修处理吗？",
            [RetrievedPolicy("POL-04", "保修范围", "擅自拆修不在免费保修范围。", 0.1)],
            "擅自拆修不在免费保修范围", "POL-04",
        ),
        (
            "申请质量售后要拍什么角度的视频、必须上传购买凭证吗？",
            [RetrievedPolicy("QUA-01", "质量售后", "需提供质量问题凭证并由人工审核。", 0.1)],
            "没有规定视频、照片或购买凭证等具体形式", "QUA-01",
        ),
        (
            "发票能不能按更高金额开，差额我可以补给你们？",
            [RetrievedPolicy("POL-09", "发票服务", "知识库未规定发票金额调整规则。", 0.1)],
            "没有规定发票金额调整规则", "POL-09",
        ),
        (
            "质量问题确认后寄回运费报销有没有固定金额上限？",
            [RetrievedPolicy("POL-05", "退换货运费", "没有固定报销上限，凭据由人工确认。", 0.1)],
            "没有规定固定报销上限", "POL-05",
        ),
        (
            "昨天付款今天没发货，是不是已经超时了？",
            [RetrievedPolicy("POL-07", "发货与物流", "通常在付款后2个工作日内发货。", 0.1)],
            "还不能判断是否超时", "POL-07",
        ),
        (
            "退款申请刚通过，我还没把商品寄回去，退款时间已经开始算了吗？",
            [RetrievedPolicy("POL-06", "退款进度", "收货并检验通过后1至3个工作日发起。", 0.1)],
            "退款计时还没有开始", "POL-06",
        ),
    ],
)
def test_oos_v2_observed_badcase_edges_have_bounded_answers(question, evidence, expected_phrase, citation):
    result = generate_answer_from_evidence(
        question, evidence=evidence, chat_model=FakeListChatModel(responses=[])
    )

    assert expected_phrase in result.answer
    assert result.citations == [citation]
    assert result.citation_check_passed is True
