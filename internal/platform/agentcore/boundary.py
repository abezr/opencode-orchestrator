from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

DecisionStatus = Literal["allowed", "approval_required", "blocked"]


@dataclass(slots=True)
class GatewayPolicyRequest:
    action_name: str
    trace_id: str
    intent: str
    user_input: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GatewayPolicyDecision:
    status: DecisionStatus
    reason: str
    gateway_name: str
    policy_name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentCoreGatewayPolicyAdapter(Protocol):
    def evaluate_action(self, request: GatewayPolicyRequest) -> GatewayPolicyDecision: ...
