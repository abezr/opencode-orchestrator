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


@dataclass(slots=True)
class ToolRegistrationRequest:
    tool_name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolRegistrationResult:
    tool_name: str
    status: str
    gateway_name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TraceEventRequest:
    trace_id: str
    event_name: str
    level: str = "info"
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TraceEventResult:
    accepted: bool
    trace_id: str
    event_name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ApprovalRequest:
    trace_id: str
    action_name: str
    reason: str
    user_input: str
    intent: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: str = "high"


@dataclass(slots=True)
class ApprovalSubmissionResult:
    status: str
    approval_id: str
    gateway_name: str
    policy_name: str
    operator_task: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentCoreGatewayPolicyAdapter(Protocol):
    def evaluate_action(self, request: GatewayPolicyRequest) -> GatewayPolicyDecision: ...

    def register_tool(self, request: ToolRegistrationRequest) -> ToolRegistrationResult: ...

    def emit_trace_event(self, request: TraceEventRequest) -> TraceEventResult: ...

    def submit_approval_request(self, request: ApprovalRequest) -> ApprovalSubmissionResult: ...
