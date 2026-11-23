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
    asks_shipping = bool(re.search(r"运费|邮费|寄回|邮寄", query))
    out_of_scope_item = "POL-01" in source_ids and bool(re.search(r"二手|第三方平台", query))

    unauthorized_repair = bool(re.search(r"自行拆修|自己拆|自己换|拆开.{0,8}(?:换|修)|改装|换了微动", query))
    if "POL-04" in source_ids and asks_warranty and unauthorized_repair:
        matched.append(AnswerConstraint(
            constraint_id="POL04_UNAUTHORIZED_REPAIR_EXCLUSION",
            instruction="POL-04 明确将擅自拆修排除在免费保修外；只说明此边界，维修方案仍需检测确认。",
            override=(
                "POL-04 明确规定，擅自拆修不在免费保修范围。是否有其他维修方案及费用，"
                "需要人工检测后确认；目前不能承诺免费处理。[POL-04]"
            ),
        ))

    if "QUA-01" in source_ids and bool(re.search(r"凭证|上传|拍摄|视频|照片|什么材料|拍什么", query)):
        matched.append(AnswerConstraint(
            constraint_id="QUA01_EVIDENCE_FORMAT_UNKNOWN",
            instruction="QUA-01 只要求提供质量问题凭证并由人工审核；不得规定视频、照片、购买凭证或拍摄形式。",
            override=(
                "规则要求提供质量问题凭证并由人工审核，但没有规定视频、照片或购买凭证等具体形式。"
                "请先联系人工确认需要提交的材料。[QUA-01]"
            ),
        ))

    if "POL-09" in source_ids and bool(re.search(r"发票|开票", query)) and bool(
        re.search(r"金额|多开|高开|差额|补给", query)
    ):
        matched.append(AnswerConstraint(
            constraint_id="POL09_INVOICE_AMOUNT_UNSPECIFIED",
            instruction="POL-09 未规定发票金额调整规则；不得声称只能按订单金额开具，也不得承诺可调整。",
            override=(
                "当前资料没有规定发票金额调整规则，我无法确认能否按更高金额开具；"
                "请联系人工核验订单。发票抬头和税号仅通过人工受理渠道提交，本聊天不收集。[POL-09]"
            ),
        ))

    if "POL-03" in source_ids and bool(re.search(r"没(?:有|货)|无库存|缺货", query)) and bool(
        re.search(r"退款|退钱|换|替代", query)
    ):
        matched.append(AnswerConstraint(
            constraint_id="POL03_NO_STOCK_NEGOTIATION",
            instruction="POL-03 规定无库存时由人工协商；不得暗示会尽快处理或承诺替代品/退款。",
            override=(
                "POL-03 规定，无库存时由人工协商处理；我不能承诺替代商品或自动退款。"
                "请联系人工核实可选方案。[POL-03]"
            ),
        ))

    if "POL-05" in source_ids and bool(re.search(r"上限|额度|报销.*(?:凭据|凭证)|(?:凭据|凭证).*报销", query)):
        matched.append(AnswerConstraint(
            constraint_id="POL05_REIMBURSEMENT_DETAILS_UNSPECIFIED",
            instruction="POL-05 未规定固定报销上限，凭据和快递渠道由人工确认；不要猜测具体金额或接受凭据类型。",
            override=(
                "POL-05 没有规定固定报销上限，报销凭据和快递渠道需由人工确认。"
                "经确认属于非人为质量问题后，标准寄回运费由企业承担；寄回前请先获取人工指引。[POL-05]"
            ),
        ))
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

    if "POL-04" in source_ids and asks_warranty and not liquid_damage and not asks_shipping and not out_of_scope_item:
        matched.append(AnswerConstraint(
            constraint_id="POL04_WARRANTY_SCOPE",
            instruction="简洁说明保修期限和适用条件；是否免费及方案需检测，避免索要订单号，除非用户要求查询具体订单。",
            override=(
                "POL-04规定，签收日起12个月内的非人为硬件故障可申请保修。"
                "需提供模拟订单供人工核验，具体方案和时间要检测后确认。[POL-04]"
            ),
        ))

    if "POL-04" in source_ids and bool(re.search(r"维修|修好|修复", query)) and bool(
        re.search(r"多久|几天|时间|什么时候|承诺|周期", query)
    ):
        matched.append(AnswerConstraint(
            constraint_id="POL04_REPAIR_TIMELINE",
            instruction="不承诺维修时限；说明维修方案和时间需检测后确认。",
            override=(
                "POL-04 没有固定维修时限。需要检测后才能确认维修方案和时间，"
                "目前无法承诺具体周期。[POL-04]"
            ),
        ))

    if (
        {"POL-01", "POL-10"}.issubset(source_ids)
        and bool(re.search(r"二手|第三方平台", query))
    ):
        international = bool(re.search(r"海外|国外|国际", query))
        scope_note = "当前资料没有国际保修规定；" if international else ""
        matched.append(AnswerConstraint(
            constraint_id="POL01_OUT_OF_SCOPE_INTERNATIONAL",
            instruction="明确二手或第三方商品不在演示政策范围；仅在问题涉及跨境/国际保修时说明当前资料没有国际条款，并建议联系原销售渠道。",
            override=(
                scope_note + "二手或第三方平台商品不在本演示政策范围内。"
                "建议向原销售渠道核实保修条件。[POL-01][POL-10]"
            ),
        ))

    if (
        "POL-08" in source_ids
        and bool(re.search(r"订单.{0,4}(?:已完成|完成了)|已完成订单", query))
        and bool(re.search(r"售后|申请", query))
    ):
        matched.append(AnswerConstraint(
            constraint_id="POL08_COMPLETED_ORDER_AFTERSALE",
            instruction="订单完成不代表售后资格失效；不要推断具体资格或擅自追问订单信息。",
            override=(
                "订单显示已完成，只表示订单流程结束；只要符合对应售后政策，仍可申请处理。"
                "具体资格要按商品和问题类型判断。[POL-08]"
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
        r"无理由|可以退|能退|想退|退货吗|退货期限|退货条件|退货申请|申请退货",
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

    if "POL-05" in source_ids and asks_shipping:
        quality_shipping = quality_issue
        if (
            quality_shipping
            and {"POL-03", "POL-05"}.issubset(source_ids)
            and not bool(re.search(r"人为损坏|进水|进液|摔坏|自行拆修", query))
        ):
            asks_collect_method = "到付" in query
            if asks_collect_method:
                override = (
                    "先不要直接寄到付件，寄回前要联系人工获取退货指引。"
                    "若经确认属于非人为质量问题，标准寄回运费由企业承担。[POL-05]"
                )
            else:
                day_match = re.search(r"签收(?:后)?第\s*(\d{1,2})\s*天", query)
                within_window = bool(day_match and int(day_match.group(1)) <= 15)
                asks_eligibility = bool(re.search(r"处理|换货|申请|售后|维修|能不能", query))
                timing = ""
                if asks_eligibility:
                    timing = (
                        f"你提到签收第{day_match.group(1)}天，仍在15个自然日内，可提交质量换货申请。"
                        if within_window else
                        "质量换货通常需在签收后15个自然日内申请。"
                    )
                override = (
                    timing + "是否属于非人为质量问题需人工检测确认；确认后标准寄回运费由企业承担。"
                    "寄回前先联系人工获取指引。[POL-03][POL-05]"
                )
            matched.append(AnswerConstraint(
                constraint_id="POL03_QUALITY_SHIPPING_SUMMARY",
                instruction="直接回答质量申请和寄回运费，不要补充无理由退货运费；故障性质须人工检测确认。",
                override=override,
            ))
            return matched
        suffix = (
            "经人工确认的非人为质量问题，标准寄回运费由企业承担；寄回前先联系人工获取退货指引。[POL-05]"
            if quality_shipping else
            "无理由退货寄回运费由用户承担；经人工确认的非人为质量问题，标准寄回运费由企业承担；"
            "寄回前先联系人工获取退货指引。[POL-05]"
        )
        matched.append(AnswerConstraint(
            constraint_id="POL05_SHIPPING_AND_GUIDANCE",
            instruction=(
                "只回答用户问到的运费类型。质量故障描述不能直接认定为非人为；应说明企业承担标准寄回运费的前提是经人工确认属于非人为质量问题。"
                "说明寄回前要获取人工指引，避免把无理由退货运费规则混入质量问题答复。"
            ),
            suffix=suffix,
        ))

    if "POL-06" in source_ids and "退款" in query and bool(re.search(r"多久|几天|到账|时间|什么时候", query)):
        not_returned_yet = bool(re.search(r"(?:还没|尚未|没有|没把).{0,8}(?:寄回|寄去|退回)|(?:寄回|寄去|退回).{0,8}(?:还没|尚未|没有)", query))
        if not_returned_yet:
            matched.append(AnswerConstraint(
                constraint_id="POL06_REFUND_CLOCK_NOT_STARTED",
                instruction="商品尚未寄回时说明退款计时尚未开始；检验通过后才进入发起阶段，不催促用户寄回。",
                override=(
                    "商品尚未寄回，退款计时还没有开始。按 POL-06，商家收货并检验通过后，"
                    "通常 1 至 3 个工作日内发起退款；发起后通常 1 至 5 个工作日到账，"
                    "不保证具体到账日。[POL-06]"
                ),
            ))
        asks_payment_channel = bool(re.search(r"银行卡|支付渠道|已退款|商家.*退|到账", query))
        matched.append(AnswerConstraint(
            constraint_id="POL06_REFUND_STAGES",
            instruction=(
                "把退款拆为检验通过后发起和发起后到账两个阶段，不能承诺具体到账日。"
                + ("如用户问商家侧状态或银行卡到账，说明已退款不等于资金到账，应以原支付渠道核实。" if asks_payment_channel else "")
            ),
            suffix=(
                ("订单显示已退款只代表商家侧处理完成，不等于资金已到账；具体入账以原支付渠道核实为准。" if asks_payment_channel else "")
                +
                "退款需在收货并检验通过后 1 至 3 个工作日内发起，"
                "发起后通常 1 至 5 个工作日到账；两个阶段分别计时，不保证具体到账日。[POL-06]"
            ),
        ))

    asks_workday_definition = bool(
        re.search(r"工作日", query)
        and re.search(r"法定节假日|节假日|周末|休息日", query)
    )
    if "POL-06" in source_ids and asks_workday_definition:
        matched.append(AnswerConstraint(
            constraint_id="POL06_WORKDAY_EXCLUDES_HOLIDAYS",
            instruction=(
                "POL-06 明确规定工作日不含周末及法定节假日。直接回答该定义，"
                "不得先说资料无法确认，也不得对证据已明确的定义拒答。"
            ),
            override=(
                "POL-06 规定，工作日不含周末及法定节假日。退款分为两个阶段："
                "收货并检验通过后 1 至 3 个工作日内发起；发起后通常 1 至 5 个工作日到账。"
                "不保证具体到账日。[POL-06]"
            ),
        ))

    if "POL-07" in source_ids and bool(re.search(r"发货|发出|没发|未发|付款后", query)):
        if bool(re.search(r"昨天.*(?:付款|支付|下单)|(?:付款|支付|下单).*昨天", query)) and bool(
            re.search(r"超时|逾期", query)
        ):
            matched.append(AnswerConstraint(
                constraint_id="POL07_NO_ORDER_STATUS_SPECULATION",
                instruction="只解释通常发货时限；没有订单状态证据时，不推测系统处理、预售或缺货。",
                override=(
                    "已付款订单通常在付款后 2 个工作日内发货。仅凭昨天付款、今天未发货，"
                    "还不能判断是否超时；我没有这笔订单的实时状态，请查询订单或联系人工核实。"
                    "发货时限不代表送达时限。[POL-07]"
                ),
            ))
        asks_delivery = bool(re.search(r"送达|到货|明天|什么时候到|几天到", query))
        matched.append(AnswerConstraint(
            constraint_id="POL07_SHIPMENT_WINDOW",
            instruction=(
                "若用户提到付款后尚未发货，说明已付款订单通常在付款后2个工作日内发货；"
                "不要把发货时限说成送达时限，也不要保证具体到货日。"
            ),
            suffix=(
                "已付款订单通常在付款后 2 个工作日内发货；"
                + (
                    "发货后通常 3 至 5 个自然日送达，仅为预计，不承诺具体到货日。"
                    + ("不能保证明天送达。" if "明天" in query else "")
                    if asks_delivery else "发货时限不代表具体送达时间。"
                )
                + "[POL-07]"
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
                if "配件" not in result:
                    missing_facts.append("配件需齐全；")
                if "包装" not in result:
                    missing_facts.append("包装需齐全；")
                if not any(term in result for term in ("再次销售", "二次销售")):
                    missing_facts.append("且不影响再次销售；")
                if not any(term in result for term in ("无人为损坏", "没有人为损坏", "非人为损坏")):
                    missing_facts.append("不得有人为损坏；")
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
            if "原支付渠道" in constraint.instruction and "支付渠道" not in result:
                missing_facts.append(
                    "订单显示已退款只代表商家侧处理完成，不等于资金已到账；具体入账以原支付渠道核实为准。"
                )
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
            if "用户承担" in (constraint.suffix or "") and not any(
                phrase in result for phrase in ("用户承担", "由您承担", "自行承担", "您先行承担")
            ):
                missing_facts.append("无理由退货寄回运费由用户承担；")
            if constraint.suffix and "企业承担" in constraint.suffix and "企业承担" not in result:
                missing_facts.append("经人工确认的非人为质量问题，标准寄回运费由企业承担；")
            if not ("人工" in result and "退货指引" in result):
                missing_facts.append("寄回前先联系人工获取退货指引，不要直接寄付到付件。")
            already_covered = not missing_facts
            suffix = "".join(missing_facts) + "[POL-05]"
        elif constraint.constraint_id == "POL07_SHIPMENT_WINDOW":
            missing_facts = []
            if not re.search(r"2\s*个工作日|两个工作日", result):
                missing_facts.append("已付款订单通常在付款后 2 个工作日内发货；")
            if "3 至 5 个自然日" in (constraint.suffix or "") and not re.search(r"3\s*至\s*5|3\s*[-–到至]\s*5", result):
                missing_facts.append("发货后通常 3 至 5 个自然日送达，仅为预计，不承诺具体到货日。")
            if "不能保证明天送达" in (constraint.suffix or "") and not re.search(r"不能.{0,6}明天|明天.{0,8}(不保证|不能保证)", result):
                missing_facts.append("不能保证明天送达。")
            already_covered = not missing_facts
            suffix = "".join(missing_facts) + "[POL-07]"
        else:
            already_covered = True
            suffix = constraint.suffix
        if not already_covered:
            addition = suffix or constraint.suffix or ""
            # The same policy may already be cited by the model answer. Keep one
            # citation and join the evidence-backed clarification into one reply.
            for source_id in re.findall(r"\[(POL-\d+)\]", addition):
                if f"[{source_id}]" in result:
                    addition = addition.replace(f"[{source_id}]", "")
            result = f"{result.rstrip()} {addition.lstrip()}" if result else addition
            enforced.append(constraint.constraint_id)

    return result, enforced
