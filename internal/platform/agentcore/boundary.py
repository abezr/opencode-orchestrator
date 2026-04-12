from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

from internal.platform.config import AgentCoreConfig

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


class ConfigBackedAgentCoreAdapter:
    def __init__(self, config: AgentCoreConfig) -> None:
        self._config = config

    def evaluate_action(self, request: GatewayPolicyRequest) -> GatewayPolicyDecision:
        metadata = {
            "agentcore_enabled": self._config.enabled,
            "action_name": request.action_name,
            "trace_id": request.trace_id,
        }
        if request.action_name in self._config.blocked_actions:
            return GatewayPolicyDecision(
                status="blocked",
                reason=f"Action '{request.action_name}' is blocked by the configured AgentCore policy contract.",
                gateway_name=self._config.gateway_name,
                policy_name=self._config.policy_name,
                metadata=metadata,
            )
        if request.action_name in self._config.approval_required_actions:
            return GatewayPolicyDecision(
                status="approval_required",
                reason=f"Action '{request.action_name}' requires approval through the configured AgentCore gateway/policy boundary.",
                gateway_name=self._config.gateway_name,
                policy_name=self._config.policy_name,
                metadata=metadata,
            )
        return GatewayPolicyDecision(
            status="allowed",
            reason=f"Action '{request.action_name}' is allowed by the configured AgentCore policy contract.",
            gateway_name=self._config.gateway_name,
            policy_name=self._config.policy_name,
            metadata=metadata,
        )
