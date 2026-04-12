from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from internal.platform.agentcore.boundary import (
    AgentCoreGatewayPolicyAdapter,
    ApprovalRequest,
    GatewayPolicyRequest,
    TraceEventRequest,
)


@dataclass(slots=True)
class SupportActionResult:
    status: str
    action_name: str
    message: str
    governance: dict[str, Any]
    operator_task: dict[str, Any] | None
    approval_submission: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SupportActionService:
    def __init__(self, agentcore: AgentCoreGatewayPolicyAdapter) -> None:
        self._agentcore = agentcore

    def request_refund_review(
        self,
        *,
        trace_id: str,
        order_id: str,
        customer_message: str,
        requested_amount: float | None,
    ) -> SupportActionResult:
        action_name = "support.request_refund"
        self._agentcore.emit_trace_event(
            TraceEventRequest(
                trace_id=trace_id,
                event_name="support.refund_review.requested",
                payload={
                    "action_name": action_name,
                    "order_id": order_id,
                    "requested_amount": requested_amount,
                },
            )
        )
        decision = self._agentcore.evaluate_action(
            GatewayPolicyRequest(
                action_name=action_name,
                trace_id=trace_id,
                intent="returns",
                user_input=customer_message,
                payload={
                    "order_id": order_id,
                    "requested_amount": requested_amount,
                },
            )
        )
        self._agentcore.emit_trace_event(
            TraceEventRequest(
                trace_id=trace_id,
                event_name="support.refund_review.decision",
                payload={
                    "action_name": action_name,
                    "decision_status": decision.status,
                },
            )
        )

        if decision.status == "blocked":
            return SupportActionResult(
                status="blocked",
                action_name=action_name,
                message="Refund request was blocked by the configured AgentCore gateway/policy boundary.",
                governance=decision.to_dict(),
                operator_task=None,
                approval_submission=None,
            )

        if decision.status == "approval_required":
            approval = self._agentcore.submit_approval_request(
                ApprovalRequest(
                    trace_id=trace_id,
                    action_name=action_name,
                    reason=decision.reason,
                    user_input=customer_message,
                    intent="returns",
                    payload={
                        "order_id": order_id,
                        "requested_amount": requested_amount,
                        "agentcore": decision.to_dict(),
                    },
                    priority="high",
                )
            )
            self._agentcore.emit_trace_event(
                TraceEventRequest(
                    trace_id=trace_id,
                    event_name="support.refund_review.approval_submitted",
                    payload={
                        "action_name": action_name,
                        "approval_id": approval.approval_id,
                    },
                )
            )
            return SupportActionResult(
                status="approval_required",
                action_name=action_name,
                message="Refund request has been submitted for approval through the AgentCore integration boundary.",
                governance=decision.to_dict(),
                operator_task=approval.operator_task,
                approval_submission=approval.to_dict(),
            )

        self._agentcore.emit_trace_event(
            TraceEventRequest(
                trace_id=trace_id,
                event_name="support.refund_review.allowed",
                payload={
                    "action_name": action_name,
                },
            )
        )
        return SupportActionResult(
            status="allowed",
            action_name=action_name,
            message="Refund action is allowed by the configured AgentCore boundary. No real side effect is executed in this scaffold.",
            governance=decision.to_dict(),
            operator_task=None,
            approval_submission=None,
        )
