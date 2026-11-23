"""Small deterministic retrieval-query rewrites for a known compound policy case."""

import re


def build_policy_retrieval_query(question: str) -> str:
    """Expand custom-product + quality + return-shipping questions into facets.

    The user-facing question is unchanged. This narrowly applies only when all
    three signals are present, so ordinary single-topic queries retain the
    existing retrieval path and configured Top-K.
    """
    custom_product = bool(re.search(r"定制|个性化", question))
    quality_issue = bool(re.search(r"质量|故障|坏了|损坏|失灵|瑕疵", question))
    shipping_cost = bool(re.search(r"运费|邮费|寄回|邮寄", question))
    if custom_product and quality_issue and shipping_cost:
        return (
            "定制商品售后适用范围 定制商品无理由退货 "
            "质量问题售后申请 15日 凭证 人工审核 "
            "退换货寄回运费承担 人工指引"
        )
    return question
