"""Typed LangChain tools bound to the authenticated demo caller."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from langchain_core.tools import StructuredTool

from support_agent.auth import DemoIdentity
from support_agent.config import Settings, get_settings
from support_agent.integrations.errors import IntegrationNotFound, IntegrationRejected
from support_agent.integrations.factory import create_mock_shop_adapter
from support_agent.integrations.mock_shop import MockShopAdapter
from support_agent.integrations.permissions import apply_webhook_order_state, can_access_order

logger = logging.getLogger(__name__)


@dataclass
class MockShopTools:
    """Tools for a single request; identity is captured server-side, never from tool args."""

    adapter: MockShopAdapter
    get_order: StructuredTool
    get_logistics: StructuredTool
    check_aftersale_eligibility: StructuredTool
    create_aftersale: StructuredTool
    get_aftersale_status: StructuredTool

    def close(self) -> None:
        self.adapter.close()


def build_mockshop_tools(
    identity: DemoIdentity,
    *,
    settings: Settings | None = None,
    adapter: MockShopAdapter | None = None,
    trace_id: str | None = None,
    database_path: Path | None = None,
) -> MockShopTools:
    """Create provider tools whose order scope is fixed to the authenticated identity."""
    settings = settings or get_settings()
    adapter = adapter or create_mock_shop_adapter(settings)
    database_path = database_path or settings.database_path

    def authorized_order(order_id: str):
        order = adapter.get_order(order_id)
        if not can_access_order(identity, order):
            raise IntegrationNotFound("Order not found for this identity")
        return apply_webhook_order_state(order, database_path)

    def _get_order(order_id: str) -> dict:
        logger.info("Agent tool called", extra={
            "event": "agent_tool_start", "trace_id": trace_id,
            "tenant_id": identity.tenant_id, "user_id": identity.user_id,
            "tool": "get_order", "order_id": order_id,
        })
        return authorized_order(order_id).model_dump()

    def _get_logistics(order_id: str) -> dict:
        logger.info("Agent tool called", extra={
            "event": "agent_tool_start", "trace_id": trace_id,
            "tenant_id": identity.tenant_id, "user_id": identity.user_id,
            "tool": "get_logistics", "order_id": order_id,
        })
        order = authorized_order(order_id)
        return adapter.get_logistics(order.order_id).model_dump()

    def _check_eligibility(order_id: str, reason: str) -> dict:
        logger.info("Agent tool called", extra={
            "event": "agent_tool_start", "trace_id": trace_id,
            "tenant_id": identity.tenant_id, "user_id": identity.user_id,
            "tool": "check_aftersale_eligibility", "order_id": order_id,
        })
        authorized_order(order_id)
        return adapter.check_aftersale_eligibility(order_id, reason).model_dump()

    def _create_aftersale(
        order_id: str, reason: str, idempotency_key: str, confirmed: bool
    ) -> dict:
        if identity.role != "requester":
            raise IntegrationRejected("Demo requester role required")
        if not confirmed:
            raise IntegrationRejected("Explicit demo confirmation is required")
        authorized_order(order_id)
        eligibility = adapter.check_aftersale_eligibility(order_id, reason)
        if not eligibility.eligible:
            raise IntegrationRejected("Order is not eligible under MockShop demo rules")
        scoped_key = hashlib.sha256(
            f"{identity.tenant_id}:{identity.user_id}:{idempotency_key}".encode("utf-8")
        ).hexdigest()
        logger.info("Agent tool called", extra={
            "event": "agent_tool_start", "trace_id": trace_id,
            "tenant_id": identity.tenant_id, "user_id": identity.user_id,
            "tool": "create_aftersale", "order_id": order_id,
        })
        return adapter.create_aftersale(order_id, reason, scoped_key).model_dump()

    def _get_aftersale_status(aftersale_id: str) -> dict:
        result = adapter.get_aftersale_status(aftersale_id)
        authorized_order(result.order_id)
        return result.model_dump()

    return MockShopTools(
        adapter=adapter,
        get_order=StructuredTool.from_function(
            func=_get_order,
            name="get_platform_order",
            description="查询当前身份有权限查看的 MockShop 虚构演示订单。参数是订单编号。",
        ),
        get_logistics=StructuredTool.from_function(
            func=_get_logistics,
            name="get_platform_logistics",
            description="查询已完成当前身份归属校验的 MockShop 演示订单物流。参数是订单编号。",
        ),
        check_aftersale_eligibility=StructuredTool.from_function(
            func=_check_eligibility,
            name="check_aftersale_eligibility",
            description="根据 MockShop 当前虚构演示规则检查售后资格；这不是审批或退款。",
        ),
        create_aftersale=StructuredTool.from_function(
            func=_create_aftersale,
            name="create_demo_aftersale",
            description="仅在请求人明确确认后创建虚构 MockShop 待处理申请，不会执行退货或退款。",
        ),
        get_aftersale_status=StructuredTool.from_function(
            func=_get_aftersale_status,
            name="get_demo_aftersale_status",
            description="查询当前身份有权访问的 MockShop 演示售后状态。",
        ),
    )
