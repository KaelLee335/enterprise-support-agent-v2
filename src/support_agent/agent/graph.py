from typing import Literal

from langgraph.graph import END, START, StateGraph

from support_agent.agent.nodes import (
    clarify_request,
    generate_policy_answer,
    lookup_order,
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
    "lookup_order", "retrieve_policy", "refuse_write_request", "clarify_request",
    "prepare_refund_approval",
]:
    return {
        "order_lookup": "lookup_order",
        "policy_qa": "retrieve_policy",
        "write_request": "refuse_write_request",
        "clarify": "clarify_request",
        "approval_required": "prepare_refund_approval",
    }.get(state.get("intent", "clarify"), "clarify_request")  # type: ignore[return-value]


def route_after_approval_precheck(
    state: SupportState,
) -> Literal["wait_for_refund_approval", "finish"]:
    return "wait_for_refund_approval" if state.get("approval_ready") else "finish"


def route_after_retrieval(state: SupportState) -> Literal["generate_policy_answer", "finish"]:
    return "generate_policy_answer" if state.get("evidence") else "finish"


def build_support_graph(
    checkpointer: BaseCheckpointSaver | None = None,
):
    builder = StateGraph(SupportState)
    nodes = {
        "route_request": route_request,
        "lookup_order": lookup_order,
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
    builder.add_edge("refuse_write_request", END)
    builder.add_edge("clarify_request", END)
    builder.add_conditional_edges(
        "retrieve_policy",
        route_after_retrieval,
        {"generate_policy_answer": "generate_policy_answer", "finish": END},
    )
    builder.add_edge("generate_policy_answer", END)
    builder.add_conditional_edges(
        "prepare_refund_approval",
        route_after_approval_precheck,
        {"wait_for_refund_approval": "wait_for_refund_approval", "finish": END},
    )
    builder.add_edge("wait_for_refund_approval", END)
    return builder.compile(checkpointer=checkpointer)
