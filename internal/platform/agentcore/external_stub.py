from __future__ import annotations

from internal.platform.agentcore.boundary import (
    AgentCoreGatewayPolicyAdapter,
    GatewayPolicyDecision,
    GatewayPolicyRequest,
)
from internal.platform.config import AgentCoreConfig


class ExternalAgentCoreAdapterStub(AgentCoreGatewayPolicyAdapter):
    def __init__(self, config: AgentCoreConfig) -> None:
        self._config = config

    def evaluate_action(self, request: GatewayPolicyRequest) -> GatewayPolicyDecision:
        metadata = {
            "integration_mode": self._config.mode,
            "base_url": self._config.base_url,
            "timeout_seconds": self._config.timeout_seconds,
            "agentcore_enabled": self._config.enabled,
            "action_name": request.action_name,
            "trace_id": request.trace_id,
        }
        if request.action_name in self._config.blocked_actions:
            return GatewayPolicyDecision(
                status="blocked",
                reason=f"External AgentCore adapter stub marked '{request.action_name}' as blocked.",
                gateway_name=self._config.gateway_name,
                policy_name=self._config.policy_name,
                metadata=metadata,
            )
        if request.action_name in self._config.approval_required_actions:
            return GatewayPolicyDecision(
                status="approval_required",
                reason=f"External AgentCore adapter stub requires approval for '{request.action_name}'.",
                gateway_name=self._config.gateway_name,
                policy_name=self._config.policy_name,
                metadata=metadata,
            )
        return GatewayPolicyDecision(
            status="allowed",
            reason=f"External AgentCore adapter stub allows '{request.action_name}'.",
            gateway_name=self._config.gateway_name,
            policy_name=self._config.policy_name,
            metadata=metadata,
        )
