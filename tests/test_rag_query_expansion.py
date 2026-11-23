from support_agent.rag.query_expansion import build_policy_retrieval_query
from support_agent.rag.retrieval import retrieve_policies


QUESTION = "键盘是定制配色，签收第4天发现按键坏了，能不能处理，邮费谁出？"


def test_compound_custom_quality_shipping_query_expands_into_policy_facets():
    expanded = build_policy_retrieval_query(QUESTION)

    assert expanded != QUESTION
    assert "定制商品无理由退货" in expanded
    assert "质量问题售后申请" in expanded
    assert "凭证" in expanded
    assert "退换货寄回运费" in expanded


def test_single_topic_query_keeps_original_retrieval_text():
    question = "键盘出现质量问题可以维修吗？"

    assert build_policy_retrieval_query(question) == question


def test_retriever_uses_expanded_text_but_preserves_top_k():
    class RecordingStore:
        query = None
        requested_k = None

        def similarity_search_with_score(self, query, k):
            self.query = query
            self.requested_k = k
            return []

    store = RecordingStore()
    assert retrieve_policies(QUESTION, store=store, top_k=4) == []

    assert store.query == build_policy_retrieval_query(QUESTION)
    assert store.requested_k == 4
