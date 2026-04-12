from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from internal.platform.agentcore.boundary import AgentCoreGatewayPolicyAdapter, GatewayPolicyRequest


@dataclass(slots=True)
class SupportActionResult:
    status: str
    action_name: str
    message: str
    governance: dict[str, Any]
    operator_task: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SupportActionService:
    def __init__(self, agentcore: AgentCoreGatewayPolicyAdapter, operator_tasks: Any) -> None:
        self._agentcore = agentcore
        self._operator_tasks = operator_tasks

    def request_refund_review(
        self,
        *,
        trace_id: str,
        order_id: str,
        customer_message: str,
        requested_amount: float | None,
    ) -> SupportActionResult:
        action_name = "support.request_refund"
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

        if decision.status == "blocked":
            return SupportActionResult(
                status="blocked",
                action_name=action_name,
                message="Refund request was blocked by the configured AgentCore gateway/policy boundary.",
                governance=decision.to_dict(),
                operator_task=None,
            )

        if decision.status == "approval_required":
            task = self._operator_tasks.enqueue(
                trace_id=trace_id,
                kind="approval_required_support_action",
                priority="high",
                reason=decision.reason,
                user_input=customer_message,
                intent="returns",
                payload={
                    "action_name": action_name,
                    "order_id": order_id,
                    "requested_amount": requested_amount,
                    "agentcore": decision.to_dict(),
                },
            )
            return SupportActionResult(
                status="approval_required",
                action_name=action_name,
                message="Refund request has been queued for approval through the AgentCore integration boundary.",
                governance=decision.to_dict(),
                operator_task=task.to_dict(),
            )

        return SupportActionResult(
            status="allowed",
            action_name=action_name,
            message="Refund action is allowed by the configured AgentCore boundary. No real side effect is executed in this scaffold.",
            governance=decision.to_dict(),
            operator_task=None,
        )
