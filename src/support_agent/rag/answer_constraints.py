"""Curated answer constraints for high-impact policy edges.

These are deliberately small, versioned application rules. They supplement
retrieved policy text and do not replace the source documents.
"""

from dataclasses import dataclass
import re

from support_agent.rag.retrieval import RetrievedPolicy


@dataclass(frozen=True)
class AnswerConstraint:
    constraint_id: str
    instruction: str
    suffix: str | None = None
    override: str | None = None
    requires_opening_clause: bool = False


def match_answer_constraints(
    question: str,
    evidence: list[RetrievedPolicy],
) -> list[AnswerConstraint]:
    source_ids = {item.source_id for item in evidence}
    query = question.lower()
    matched: list[AnswerConstraint] = []

    liquid_damage = bool(re.search(r"进水|进液|液体|液体损坏", query))
    asks_warranty = bool(re.search(r"保修|质保|免费维修|免费修", query))
    if "POL-04" in source_ids and liquid_damage and asks_warranty:
        matched.append(AnswerConstraint(
            constraint_id="POL04_LIQUID_EXCLUSION",
            instruction=(
                "POL-04 明确排除进液造成的免费保修。不得称此情况可申请免费保修；"
                "只说明排除条款和检测后才能确认的维修方案。"
            ),
            override=(
                "POL-04 明确规定，进液导致的损坏不在免费保修范围。"
                "维修方案和时间需检测后确认，不能仅凭描述承诺。"
                "如需了解可行方案，请联系人工售后核验。[POL-04]"
            ),
        ))

    quality_issue = bool(re.search(r"质量问题|质量故障|故障|失灵|损坏|坏了|无法使用", query))
    asks_return = bool(re.search(r"退货|能退|可以退|退吗", query))
    if quality_issue and asks_return and "POL-02" in source_ids:
        matched.append(AnswerConstraint(
            constraint_id="POL02_QUALITY_ROUTE",
            instruction=(
                "问题描述为质量故障时，不得只按无理由退货期限判断。"
                "POL-02 指向 POL-04/POL-05 处理质量问题；说明需按质量规则人工核验，申请不等于批准。"
            ),
            override=(
                "你描述的是质量问题，不能仅按无理由退货期限判断。POL-02 规定质量问题按"
                " POL-04/POL-05 规则处理；申请不等于批准，需人工核验。"
                "当前资料不足以承诺退货或换货获批。[POL-02]"
            ),
        ))

    asks_return_eligibility = bool(re.search(
        r"无理由|可以退|能退|退货吗|退货期限|退货条件|退货申请|申请退货",
        query,
    ))
    if (
        "POL-02" in source_ids
        and asks_return_eligibility
        and not (quality_issue and asks_return)
    ):
        matched.append(AnswerConstraint(
            constraint_id="POL02_RETURN_CONDITIONS",
            instruction=(
                "回答无理由退货时应说明申请期限、商品/包装条件、再次销售条件和人工检查；"
                "申请不是批准。只陈述本轮问题涉及且证据支持的内容。"
            ),
            suffix=(
                "无理由退货还要求配件、包装齐全，无人为损坏且不影响再次销售；"
                "拆封本身不自动拒绝，是否影响再次销售由人工检查。提交申请不等于批准，需人工核验。[POL-02]"
            ),
            requires_opening_clause="拆封" in query,
            # These phrases cover the core qualifier set without requiring one
            # exact wording from the model.
        ))

    if "POL-05" in source_ids and bool(re.search(r"运费|邮费|寄回|邮寄", query)):
        quality_shipping = quality_issue
        suffix = (
            "无理由退货寄回运费由用户承担；"
            + (
                "经人工确认的非人为质量问题，标准寄回运费由企业承担；"
                if quality_shipping else ""
            )
            + "寄回前先联系人工获取退货指引，不要直接寄付到付件。[POL-05]"
        )
        matched.append(AnswerConstraint(
            constraint_id="POL05_SHIPPING_AND_GUIDANCE",
            instruction=(
                "准确区分无理由退货和经人工确认的质量问题运费责任，并说明先获取人工退货指引。"
            ),
            suffix=suffix,
        ))

    if "POL-06" in source_ids and "退款" in query and bool(re.search(r"多久|几天|到账|时间|什么时候", query)):
        matched.append(AnswerConstraint(
            constraint_id="POL06_REFUND_STAGES",
            instruction=(
                "把退款拆为检验通过后发起和发起后到账两个阶段，不能承诺具体到账日。"
            ),
            suffix=(
                "退款需在收货并检验通过后 1 至 3 个工作日内发起，"
                "发起后通常 1 至 5 个工作日到账；两个阶段分别计时，不保证具体到账日。[POL-06]"
            ),
        ))

    if "POL-09" in source_ids and bool(re.search(r"发票|专票|税号|抬头|开票", query)):
        if bool(re.search(r"抬头|税号|重开|重新开", query)):
            suffix = (
                "是否可重开需人工核验订单；发票抬头与税号仅在人工受理渠道提交，"
                "本聊天不收集。[POL-09]"
            )
            override = (
                "当前政策未明确能否重开发票抬头，需人工核验订单。"
                "发票抬头与税号仅在人工受理渠道提交，本聊天不收集。[POL-09]"
            )
        elif bool(re.search(r"专票|多久|几天|时效|时间|保证", query)):
            suffix = (
                "当前资料未规定专票资格或开票时效，无法确认；需人工核验订单。"
                "发票抬头与税号仅在人工受理渠道提交，本聊天不收集。[POL-09]"
            )
            override = suffix
        else:
            suffix = "发票抬头与税号仅在人工受理渠道提交，本聊天不收集。[POL-09]"
            override = None
        matched.append(AnswerConstraint(
            constraint_id="POL09_INVOICE_PRIVACY_AND_SCOPE",
            instruction=(
                "不得编造开票时效或专票资格。明确发票抬头和税号只能通过人工受理渠道提交，"
                "不要在本聊天中索取。"
            ),
            suffix=suffix,
            override=override,
        ))

    return matched


def apply_answer_constraints(
    answer: str,
    constraints: list[AnswerConstraint],
) -> tuple[str, list[str]]:
    """Enforce hard exclusions and add canonical facts the model omitted."""
    for constraint in constraints:
        if constraint.override is not None:
            return constraint.override, [constraint.constraint_id]

    enforced: list[str] = []
    result = answer.strip()
    for constraint in constraints:
        if constraint.suffix is None:
            continue
        if constraint.constraint_id == "POL02_RETURN_CONDITIONS":
            return_declined = bool(re.search(
                r"超过.{0,3}(?:7|七)天|已超期|超过期限|无法进行无理由退货|不能按无理由退货",
                result,
            ))
            missing_facts = []
            if not return_declined:
                if not all(term in result for term in ("配件", "包装", "再次销售")):
                    missing_facts.append(
                        "商品须配件、包装齐全，无人为损坏且不影响再次销售。"
                    )
                if constraint.requires_opening_clause and "拆封本身" not in result:
                    missing_facts.append(
                        "拆封本身不自动拒绝；是否影响再次销售由人工检查。"
                    )
                if not any(term in result for term in ("人工检查", "人工核验")):
                    missing_facts.append("商品状态需人工检查并核验。")
                if not any(term in result for term in (
                    "申请不是批准", "申请不等于批准", "不等于批准", "不代表批准"
                )):
                    missing_facts.append("提交申请不等于批准。")
            already_covered = return_declined or not missing_facts
            suffix = "".join(missing_facts) + "[POL-02]"
        elif constraint.constraint_id == "POL06_REFUND_STAGES":
            missing_facts = []
            if not re.search(r"1\s*至\s*3|1\s*[-–至]\s*3", result):
                missing_facts.append("检验通过后 1 至 3 个工作日内发起退款；")
            if not re.search(r"1\s*至\s*5|1\s*[-–至]\s*5", result):
                missing_facts.append("发起后通常 1 至 5 个工作日到账；")
            if not re.search(
                r"不保证|不能保证|无法保证|无法确定.{0,8}到账|具体到账时间无法确定",
                result,
            ):
                missing_facts.append("不保证具体到账日。")
            already_covered = not missing_facts
            suffix = "".join(missing_facts) + "[POL-06]"
        elif constraint.constraint_id == "POL09_INVOICE_PRIVACY_AND_SCOPE":
            missing_facts = []
            if not any(term in result for term in ("人工受理渠道", "人工渠道")):
                missing_facts.append("相关信息仅通过人工受理渠道提交；")
            if not any(term in result for term in ("不收集", "不要提供", "不要在聊天")) and not re.search(
                r"不在.{0,8}聊天中收集", result
            ):
                missing_facts.append("本聊天不收集发票抬头和税号。")
            already_covered = not missing_facts
            suffix = "".join(missing_facts) + "[POL-09]"
        elif constraint.constraint_id == "POL05_SHIPPING_AND_GUIDANCE":
            missing_facts = []
            if "用户承担" not in result:
                missing_facts.append("无理由退货寄回运费由用户承担；")
            if constraint.suffix and "企业承担" in constraint.suffix and "企业承担" not in result:
                missing_facts.append("经人工确认的非人为质量问题，标准寄回运费由企业承担；")
            if not ("人工" in result and "退货指引" in result):
                missing_facts.append("寄回前先联系人工获取退货指引，不要直接寄付到付件。")
            already_covered = not missing_facts
            suffix = "".join(missing_facts) + "[POL-05]"
        else:
            already_covered = True
            suffix = constraint.suffix
        if not already_covered:
            addition = suffix or constraint.suffix or ""
            result = f"{result}\n\n{addition}" if result else addition
            enforced.append(constraint.constraint_id)

    return result, enforced
