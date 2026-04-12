from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from internal.platform.agentcore.boundary import (
    AgentCoreGatewayPolicyAdapter,
    ApprovalRequest,
    ApprovalSubmissionResult,
    GatewayPolicyDecision,
    GatewayPolicyRequest,
    ToolRegistrationRequest,
    ToolRegistrationResult,
    TraceEventRequest,
    TraceEventResult,
)
from internal.platform.config import AgentCoreConfig


class ExternalAgentCoreAdapterStub(AgentCoreGatewayPolicyAdapter):
    def __init__(self, config: AgentCoreConfig, operator_tasks: Any) -> None:
        self._config = config
        self._operator_tasks = operator_tasks
        self._registered_tools: dict[str, dict[str, Any]] = {}
        self._trace_events: deque[dict[str, Any]] = deque(maxlen=200)
        self._approval_submissions: deque[dict[str, Any]] = deque(maxlen=200)

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

    def register_tool(self, request: ToolRegistrationRequest) -> ToolRegistrationResult:
        status = "registered"
        if request.tool_name in self._registered_tools:
            status = "already_registered"
        self._registered_tools[request.tool_name] = {
            "tool_name": request.tool_name,
            "description": request.description,
            "input_schema": request.input_schema,
            "metadata": request.metadata,
            "gateway_name": self._config.gateway_name,
            "registered_at": datetime.now(UTC).isoformat(),
        }
        return ToolRegistrationResult(
            tool_name=request.tool_name,
            status=status,
            gateway_name=self._config.gateway_name,
            metadata={
                "integration_mode": self._config.mode,
                "base_url": self._config.base_url,
            },
        )

    def emit_trace_event(self, request: TraceEventRequest) -> TraceEventResult:
        event = {
            "trace_id": request.trace_id,
            "event_name": request.event_name,
            "level": request.level,
            "payload": request.payload,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._trace_events.appendleft(event)
        return TraceEventResult(
            accepted=True,
            trace_id=request.trace_id,
            event_name=request.event_name,
            metadata={
                "integration_mode": self._config.mode,
                "base_url": self._config.base_url,
            },
        )

    def submit_approval_request(self, request: ApprovalRequest) -> ApprovalSubmissionResult:
        approval_id = str(uuid4())
        task = self._operator_tasks.enqueue(
            trace_id=request.trace_id,
            kind="approval_required_support_action",
            priority=request.priority,
            reason=request.reason,
            user_input=request.user_input,
            intent=request.intent,
            payload={
                "approval_id": approval_id,
                "action_name": request.action_name,
                **request.payload,
            },
        )
        submission = {
            "approval_id": approval_id,
            "trace_id": request.trace_id,
            "action_name": request.action_name,
            "status": "submitted",
            "created_at": datetime.now(UTC).isoformat(),
            "operator_task_id": task.id,
        }
        self._approval_submissions.appendleft(submission)
        return ApprovalSubmissionResult(
            status="submitted",
            approval_id=approval_id,
            gateway_name=self._config.gateway_name,
            policy_name=self._config.policy_name,
            operator_task=task.to_dict(),
            metadata={
                "integration_mode": self._config.mode,
                "base_url": self._config.base_url,
            },
        )

    def snapshot_state(self) -> dict[str, Any]:
        return {
            "registered_tools": list(self._registered_tools.values()),
            "trace_events": list(self._trace_events),
            "approval_submissions": list(self._approval_submissions),
        }
