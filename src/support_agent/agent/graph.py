from typing import Literal

from langgraph.graph import END, START, StateGraph

from support_agent.agent.nodes import (
    clarify_request,
    check_mockshop_aftersale,
    compose_mockshop_aftersale_guidance,
    generate_policy_answer,
    lookup_order,
    lookup_logistics,
    lookup_mockshop_logistics,
    lookup_mockshop_order,
    refuse_write_request,
    retrieve_policy,
    route_request,
    prepare_refund_approval,
    wait_for_refund_approval,
)
from support_agent.agent.state import SupportState
from langgraph.checkpoint.base import BaseCheckpointSaver
from support_agent.observability import traced_node


def route_by_intent(state: SupportState) -> Literal[
    "lookup_order", "lookup_logistics", "retrieve_policy", "refuse_write_request", "clarify_request",
    "prepare_refund_approval", "lookup_mockshop_order", "lookup_mockshop_logistics",
    "check_mockshop_aftersale",
]:
    return {
        "order_lookup": "lookup_order",
        "logistics_lookup": "lookup_logistics",
        "policy_qa": "retrieve_policy",
        "write_request": "refuse_write_request",
        "clarify": "clarify_request",
        "approval_required": "prepare_refund_approval",
        "mockshop_order_lookup": "lookup_mockshop_order",
        "mockshop_logistics_lookup": "lookup_mockshop_logistics",
        "mockshop_aftersale_check": "check_mockshop_aftersale",
    }.get(state.get("intent", "clarify"), "clarify_request")  # type: ignore[return-value]


def route_after_approval_precheck(
    state: SupportState,
) -> Literal["wait_for_refund_approval", "finish"]:
    return "wait_for_refund_approval" if state.get("approval_ready") else "finish"


def route_after_retrieval(
    state: SupportState,
) -> Literal["generate_policy_answer", "compose_mockshop_aftersale_guidance", "finish"]:
    if state.get("intent") == "mockshop_aftersale_check" and not state.get("evidence"):
        return "compose_mockshop_aftersale_guidance"
    return "generate_policy_answer" if state.get("evidence") else "finish"


def route_after_mockshop_check(
    state: SupportState,
) -> Literal["retrieve_policy", "finish"]:
    return "retrieve_policy" if state.get("platform_order") and state.get("aftersale_eligibility") else "finish"


def route_after_policy_answer(state: SupportState) -> Literal["compose_mockshop_aftersale_guidance", "finish"]:
    return "compose_mockshop_aftersale_guidance" if state.get("intent") == "mockshop_aftersale_check" else "finish"


def build_support_graph(
    checkpointer: BaseCheckpointSaver | None = None,
):
    builder = StateGraph(SupportState)
    nodes = {
        "route_request": route_request,
        "lookup_order": lookup_order,
        "lookup_logistics": lookup_logistics,
        "lookup_mockshop_order": lookup_mockshop_order,
        "lookup_mockshop_logistics": lookup_mockshop_logistics,
        "check_mockshop_aftersale": check_mockshop_aftersale,
        "compose_mockshop_aftersale_guidance": compose_mockshop_aftersale_guidance,
        "retrieve_policy": retrieve_policy,
        "generate_policy_answer": generate_policy_answer,
        "refuse_write_request": refuse_write_request,
        "clarify_request": clarify_request,
        "prepare_refund_approval": prepare_refund_approval,
        "wait_for_refund_approval": wait_for_refund_approval,
    }
    for name, node_fn in nodes.items():
        builder.add_node(name, traced_node(name, node_fn))
    builder.add_edge(START, "route_request")
    builder.add_conditional_edges("route_request", route_by_intent)
    builder.add_edge("lookup_order", END)
    builder.add_edge("lookup_logistics", END)
    builder.add_edge("lookup_mockshop_order", END)
    builder.add_edge("lookup_mockshop_logistics", END)
    builder.add_conditional_edges(
        "check_mockshop_aftersale",
        route_after_mockshop_check,
        {"retrieve_policy": "retrieve_policy", "finish": END},
    )
    builder.add_edge("refuse_write_request", END)
    builder.add_edge("clarify_request", END)
    builder.add_conditional_edges(
        "retrieve_policy",
        route_after_retrieval,
        {
            "generate_policy_answer": "generate_policy_answer",
            "compose_mockshop_aftersale_guidance": "compose_mockshop_aftersale_guidance",
            "finish": END,
        },
    )
    builder.add_conditional_edges(
        "generate_policy_answer",
        route_after_policy_answer,
        {"compose_mockshop_aftersale_guidance": "compose_mockshop_aftersale_guidance", "finish": END},
    )
    builder.add_edge("compose_mockshop_aftersale_guidance", END)
    builder.add_conditional_edges(
        "prepare_refund_approval",
        route_after_approval_precheck,
        {"wait_for_refund_approval": "wait_for_refund_approval", "finish": END},
    )
    builder.add_edge("wait_for_refund_approval", END)
    return builder.compile(checkpointer=checkpointer)
