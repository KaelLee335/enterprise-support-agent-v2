import logging
import re
from typing import Any

from pathlib import Path
from langgraph.types import interrupt

from support_agent.config import get_settings
from support_agent.db import fetch_order
from support_agent.logistics import fetch_shipment
from support_agent.rag.answer import create_siliconflow_chat_model, generate_answer_from_evidence
from support_agent.rag.retrieval import (
    RetrievedPolicy,
    create_siliconflow_embeddings,
    retrieve_policies,
)
from support_agent.rag.index import open_policy_store

logger = logging.getLogger(__name__)
ORDER_ID_CANDIDATE_PATTERN = re.compile(r"(?<![A-Z0-9-])[A-Z0-9][A-Z0-9-]{3,}(?![A-Z0-9-])")
ORDER_ID_PATTERN = re.compile(r"(?<![A-Z0-9-])(?:DEMO202611\d{4}|\d{4})(?![A-Z0-9-])")
PRIVACY_REQUEST_PATTERN = re.compile(
    r"(?:電話|手机号|手機號|收件地址|收件电话|收件電話|邮箱|郵箱|身份证|身份證)"
)
PROMPT_INJECTION_PATTERN = re.compile(
    r"(?:忽略|无视|無視).{0,12}(?:系统|系統|规则|規則)|"
    r"(?:伪造|偽造).{0,12}(?:政策|编号|編號)|"
    r"(?:声称|說|说).{0,8}(?:已转人工|已轉人工|已经转人工|已經轉人工)"
)
WRITE_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"帮我(?:直接|马上|立即|办理|执行|发起)?(?:退款|退钱|改地址|修改地址|取消订单)",
    r"(?:直接|马上|立即)(?:给我)?(?:退款|退钱|改地址|修改地址|取消)",
    r"(?:把|将).{0,16}(?:地址改|改地址|取消订单|退掉订单)",
    r"(?:把|将).{0,30}(?:改成|设置为).{0,12}(?:已退款|退款成功|已取消)",
    r"(?:替我|帮我)(?:取消|删除|修改)",
    r"(?:给|对)\s*(?:订单\s*)?[A-Z0-9][A-Z0-9-]{3,}.{0,8}(?:退款|退钱|改地址|修改地址|取消)",
))
ORDER_LOOKUP_TERMS = ("查", "查询", "订单", "状态", "物流", "退款到哪")
LOGISTICS_TERMS = ("物流", "快递", "运到哪", "到哪了", "配送进度")


def route_request(state: dict[str, Any]) -> dict[str, Any]:
    question = state["question"].strip()
    if PRIVACY_REQUEST_PATTERN.search(question):
        result = {"intent": "write_request", "order_id": None, "refusal_reason": "privacy_request"}
        logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
        return result
    if PROMPT_INJECTION_PATTERN.search(question):
        result = {"intent": "write_request", "order_id": None, "refusal_reason": "prompt_injection"}
        logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
        return result

    order_candidates = ORDER_ID_CANDIDATE_PATTERN.findall(question.upper())
    valid_order_ids = ORDER_ID_PATTERN.findall(question.upper())
    if len(valid_order_ids) > 1:
        result = {"intent": "clarify", "order_id": None, "clarify_reason": "multiple_order_ids"}
        logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
        return result
    if order_candidates and not valid_order_ids:
        result = {"intent": "clarify", "order_id": None, "clarify_reason": "invalid_order_id"}
        logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
        return result
    if any(pattern.search(question) for pattern in WRITE_PATTERNS):
        order_match = ORDER_ID_PATTERN.search(question.upper())
        if re.search(r"(?:改成|设置为).{0,12}(?:已退款|退款成功|已取消)", question):
            result = {"intent": "write_request", "order_id": None}
            logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
            return result
        if "退款" in question or "退钱" in question:
            result = {
                "intent": "approval_required",
                "order_id": order_match.group(0) if order_match else None,
                "requested_action": "refund",
            }
            logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
            return result
        return {"intent": "write_request", "order_id": None}

    order_match = ORDER_ID_PATTERN.search(question.upper())
    wants_order_status = any(term in question for term in ORDER_LOOKUP_TERMS)
    if order_match and any(term in question for term in LOGISTICS_TERMS):
        result = {"intent": "logistics_lookup", "order_id": order_match.group(0)}
        logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
        return result
    if order_match and wants_order_status:
        result = {"intent": "order_lookup", "order_id": order_match.group(0)}
        logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
        return result
    if order_match or "订单" in question or wants_order_status:
        result = {"intent": "clarify", "order_id": order_match.group(0) if order_match else None}
    else:
        result = {"intent": "policy_qa", "order_id": None}
    logger.info("Request routed", extra={"event": "agent_route", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "intent": result["intent"]})
    return result


def lookup_order(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    try:
        order = fetch_order(
            Path(state.get("database_path", str(settings.database_path))),
            str(state["order_id"]),
            state["tenant_id"],
        )
    except Exception as exc:  # Database failure becomes an observable safe answer.
        logger.exception("Order lookup failed")
        return {
            "order": None,
            "answer": "订单查询暂时不可用，请稍后再试。",
            "error": type(exc).__name__,
        }
    if order is None:
        return {
            "order": None,
            "answer": "未找到当前租户下的该订单。",
            "error": None,
        }
    return {
        "order": order,
        "answer": (
            f"订单 {order['order_id']} 是只读演示查询，当前状态：{order['status']}。"
            "查询不会执行退款或修改操作。"
        ),
        "error": None,
    }


def lookup_logistics(state: dict[str, Any]) -> dict[str, Any]:
    """Tenant-check the fictional order before calling the mock shipping service."""
    settings = get_settings()
    try:
        order = fetch_order(
            Path(state.get("database_path", str(settings.database_path))),
            str(state["order_id"]),
            state["tenant_id"],
        )
        if order is None:
            return {"order": None, "shipment": None, "answer": "未找到当前租户下的该订单。", "error": None}
        shipment = fetch_shipment(str(state["order_id"]), settings)
    except Exception as exc:
        logger.exception("Demo logistics lookup failed")
        return {
            "order": None,
            "shipment": None,
            "answer": "演示物流服务暂时不可用，请稍后再试；未获取真实物流信息。",
            "error": type(exc).__name__,
        }
    return {
        "order": order,
        "shipment": shipment.model_dump(),
        "answer": (
            f"订单 {shipment.order_id} 的演示物流状态：{shipment.status}。"
            f"演示运单号：{shipment.tracking_number}。该信息为本地虚构数据。"
        ),
        "error": None,
    }


def refuse_write_request(state: dict[str, Any]) -> dict[str, Any]:
    reason = state.get("refusal_reason")
    if reason == "privacy_request":
        answer = "我不能提供或泄露订单中的个人联系信息。"
    elif reason == "prompt_injection":
        answer = "我会遵循系统和业务规则，不能伪造政策引用或声称已转接人工。"
    else:
        answer = "我只能进行只读查询，不能执行退款、改址、取消或删除操作。"
    return {
        "answer": answer,
        "order": None,
        "error": None,
    }


def prepare_refund_approval(state: dict[str, Any]) -> dict[str, Any]:
    order_id = state.get("order_id")
    if not order_id:
        return {
            "approval_ready": False,
            "approval_status": "missing_order_id",
            "pending_action": None,
            "answer": "退款请求需要先提供订单号；此演示不会执行真实退款。",
            "error": None,
        }
    settings = get_settings()
    try:
        order = fetch_order(
            Path(state.get("database_path", str(settings.database_path))),
            str(order_id),
            state["tenant_id"],
        )
    except Exception as exc:
        logger.exception("Refund approval precheck failed")
        return {
            "approval_ready": False,
            "approval_status": "error",
            "pending_action": None,
            "answer": "暂时无法核对订单，未创建审批请求。",
            "error": type(exc).__name__,
        }
    if order is None:
        return {
            "approval_ready": False,
            "approval_status": "order_not_found",
            "pending_action": None,
            "answer": "未找到当前租户下的该订单，未创建审批请求。",
            "error": None,
        }
    pending_action = {
        "action": "refund_review",
        "order_id": str(order_id),
        "order_status": str(order["status"]),
        "demo_only": True,
    }
    return {
        "approval_ready": True,
        "approval_status": "pending",
        "pending_action": pending_action,
        "answer": "退款请求已暂停，等待人工审批。该演示不会执行真实退款或修改订单。",
        "error": None,
    }


def wait_for_refund_approval(state: dict[str, Any]) -> dict[str, Any]:
    decision = interrupt({
        "type": "refund_approval",
        "pending_action": state["pending_action"],
        "message": "请由人工审批此演示请求。批准只记录演示状态，不执行真实退款。",
    })
    approved = bool(decision.get("approved")) if isinstance(decision, dict) else False
    if approved:
        return {
            "approval_status": "approved_demo",
            "answer": "人工已批准该演示请求；只记录批准状态，未执行真实退款或修改订单。",
        }
    return {
        "approval_status": "rejected",
        "answer": "人工已拒绝该演示请求；订单未修改，也未执行退款。",
    }


def clarify_request(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("clarify_reason") == "multiple_order_ids":
        return {"answer": "请一次只提供一个订单号，以便准确查询。", "order": None, "error": None}
    if state.get("clarify_reason") == "invalid_order_id":
        return {"answer": "订单号格式不正确，请核对后重新提供。", "order": None, "error": None}
    if state.get("order_id"):
        answer = f"收到订单号 {state['order_id']}。请说明你要查询订单状态、物流还是退款进度。"
    else:
        answer = "请提供订单号，并说明要查询的订单信息。"
    return {"answer": answer, "order": None, "error": None}


def retrieve_policy(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    try:
        embeddings = create_siliconflow_embeddings(settings)
        store = open_policy_store(
            settings.vector_store_path,
            embeddings,
            embedding_model=settings.siliconflow_embedding_model,
        )
        evidence = retrieve_policies(
            state["question"], store=store, top_k=settings.rag_top_k
        )
    except Exception as exc:
        logger.exception("Policy retrieval failed")
        return {"evidence": [], "answer": "政策检索暂时不可用，无法确认。", "error": type(exc).__name__}
    result = {
        "evidence": [item.__dict__ for item in evidence],
        "error": None,
    }
    logger.info("Policies retrieved", extra={"event": "rag_retrieval", "trace_id": state.get("trace_id"), "tenant_id": state.get("tenant_id"), "source_count": len(evidence)})
    return result


def generate_policy_answer(state: dict[str, Any]) -> dict[str, Any]:
    evidence = [RetrievedPolicy(**item) for item in state.get("evidence", [])]
    if not evidence:
        return {
            "answer": "当前政策资料没有检索到可用依据，暂时无法确认。",
            "citations": [],
            "citations_valid": False,
        }
    try:
        result = generate_answer_from_evidence(
            state["question"],
            evidence=evidence,
            chat_model=create_siliconflow_chat_model(),
        )
    except Exception as exc:
        logger.exception("Policy answer generation failed")
        return {
            "answer": "回答服务暂时不可用，当前无法确认政策内容。",
            "citations": [],
            "citations_valid": False,
            "error": type(exc).__name__,
        }
    logger.info(
        "Policy answer constraints applied",
        extra={
            "event": "rag_answer_constraints",
            "matched_constraint_ids": result.constraint_ids,
            "enforced_constraint_ids": result.enforced_constraint_ids,
        },
    )
    if not result.citation_check_passed:
        return {
            "answer": "生成的回答未能通过来源编号检查，请结合下方检索证据人工核验。",
            "citations": result.citations,
            "citations_valid": False,
        }
    return {
        "answer": result.answer,
        "citations": result.citations,
        "citations_valid": True,
    }
