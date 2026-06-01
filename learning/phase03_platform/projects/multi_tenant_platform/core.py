"""阶段三综合项目：多租户 Agent 平台请求准入。"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any


ROLE_ACTIONS = {
    "viewer": {"read"},
    "editor": {"read", "draft"},
    "admin": {"read", "draft", "manage_members"},
}


@dataclass(frozen=True)
class UserContext:
    """经过身份认证后传给平台服务的上下文。"""

    user_id: str  # 当前用户稳定 ID。
    tenant_id: str  # 当前请求所属租户。
    role: str  # 当前用户在租户中的角色。


@dataclass(frozen=True)
class Document:
    """知识库中的租户私有文档。"""

    document_id: str  # 文档稳定 ID。
    tenant_id: str  # 文档所属租户。
    title: str  # 文档标题。


@dataclass(frozen=True)
class AccessDecision:
    """平台请求准入结果。"""

    allowed: bool  # 是否允许继续调用模型或工具。
    reason: str  # 允许或拒绝的原因。
    remaining_budget: float  # 当前租户剩余预算。


class TenantPlatform:
    """将权限、限流、预算和审计放在模型调用之前。"""

    def __init__(self, request_limit: int = 2, window_seconds: int = 60) -> None:
        self.request_limit = request_limit  # 单租户窗口请求上限。
        self.window_seconds = window_seconds  # 限流窗口长度。
        self.events: dict[str, deque[float]] = defaultdict(deque)  # 租户请求时间。
        self.budgets: dict[str, float] = defaultdict(float)  # 租户剩余预算。
        self.documents: list[Document] = []  # 教学用内存知识库。
        self.audit_log: list[dict[str, Any]] = []  # 教学用审计事件。

    def set_budget(self, tenant_id: str, amount: float) -> None:
        self.budgets[tenant_id] = round(amount, 6)

    def add_document(self, document: Document) -> None:
        self.documents.append(document)

    def list_documents(self, context: UserContext) -> list[Document]:
        """始终按服务端 tenant_id 过滤文档。"""

        return [item for item in self.documents if item.tenant_id == context.tenant_id]

    def authorize(self, context: UserContext, action: str, estimated_cost: float, now: float) -> AccessDecision:
        """在模型调用前执行权限、限流和预算检查。"""

        if action not in ROLE_ACTIONS.get(context.role, set()):
            return self._record(context, False, "角色无权执行该动作")
        tenant_events = self.events[context.tenant_id]
        while tenant_events and tenant_events[0] <= now - self.window_seconds:
            tenant_events.popleft()
        if len(tenant_events) >= self.request_limit:
            return self._record(context, False, "租户请求频率超过限制")
        if self.budgets[context.tenant_id] < estimated_cost:
            return self._record(context, False, "租户预算不足")
        tenant_events.append(now)
        self.budgets[context.tenant_id] = round(self.budgets[context.tenant_id] - estimated_cost, 6)
        return self._record(context, True, "准入检查通过")

    def _record(self, context: UserContext, allowed: bool, reason: str) -> AccessDecision:
        decision = AccessDecision(allowed, reason, self.budgets[context.tenant_id])
        self.audit_log.append({"context": asdict(context), "decision": asdict(decision)})
        return decision
