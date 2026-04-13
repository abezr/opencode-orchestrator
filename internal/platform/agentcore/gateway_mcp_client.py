from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx

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


class AgentCoreGatewayMCPClient(AgentCoreGatewayPolicyAdapter):
    def __init__(self, config: AgentCoreConfig, fallback_adapter: AgentCoreGatewayPolicyAdapter | None = None) -> None:
        self._config = config
        self._fallback_adapter = fallback_adapter
        self._events: deque[dict[str, Any]] = deque(maxlen=200)
        self._trace_events: deque[dict[str, Any]] = deque(maxlen=200)
        self._tool_registrations: deque[dict[str, Any]] = deque(maxlen=50)

    def evaluate_action(self, request: GatewayPolicyRequest) -> GatewayPolicyDecision:
        return GatewayPolicyDecision(
            status="approval_required",
            reason=(
                f"Gateway policy for '{request.action_name}' is enforced at the real AgentCore Gateway tool boundary; "
                "the final allow or deny decision happens during the MCP tool call."
            ),
            gateway_name=self._config.gateway_name,
            policy_name=self._config.policy_name,
            metadata={
                "mode": self._config.mode,
                "gateway_url": self._config.gateway_url,
                "tool_name": self._config.refund_tool_name,
            },
        )

    def register_tool(self, request: ToolRegistrationRequest) -> ToolRegistrationResult:
        record = {
            "tool_name": request.tool_name,
            "description": request.description,
            "input_schema": request.input_schema,
            "metadata": request.metadata,
            "registered_at": datetime.now(UTC).isoformat(),
            "status": "out_of_band",
        }
        self._tool_registrations.appendleft(record)
        return ToolRegistrationResult(
            tool_name=request.tool_name,
            status="out_of_band",
            gateway_name=self._config.gateway_name,
            metadata={
                "mode": self._config.mode,
                "gateway_url": self._config.gateway_url,
                "note": "Tool registration is managed in AWS Gateway configuration, not via runtime MCP calls.",
            },
        )

    def emit_trace_event(self, request: TraceEventRequest) -> TraceEventResult:
        self._trace_events.appendleft(
            {
                "trace_id": request.trace_id,
                "event_name": request.event_name,
                "level": request.level,
                "payload": request.payload,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        return TraceEventResult(
            accepted=True,
            trace_id=request.trace_id,
            event_name=request.event_name,
            metadata={
                "mode": self._config.mode,
                "gateway_url": self._config.gateway_url,
                "note": "Trace event accepted locally; production forwarding can be added to CloudWatch or AgentCore Observability later.",
            },
        )

    def submit_approval_request(self, request: ApprovalRequest) -> ApprovalSubmissionResult:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": "tools/call",
            "params": {
                "name": self._config.refund_tool_name,
                "arguments": {
                    "trace_id": request.trace_id,
                    "reason": request.reason,
                    "user_input": request.user_input,
                    "intent": request.intent,
                    **request.payload,
                },
            },
        }
        try:
            response_json = self._post_mcp(payload)
            if "error" in response_json:
                return ApprovalSubmissionResult(
                    status="denied",
                    approval_id=str(uuid4()),
                    gateway_name=self._config.gateway_name,
                    policy_name=self._config.policy_name,
                    operator_task=None,
                    metadata={
                        "mode": self._config.mode,
                        "gateway_url": self._config.gateway_url,
                        "gateway_error": response_json["error"],
                    },
                )
            result_payload = response_json.get("result")
            approval_id = str(uuid4())
            return ApprovalSubmissionResult(
                status="submitted",
                approval_id=approval_id,
                gateway_name=self._config.gateway_name,
                policy_name=self._config.policy_name,
                operator_task=result_payload if isinstance(result_payload, dict) else {"result": result_payload},
                metadata={
                    "mode": self._config.mode,
                    "gateway_url": self._config.gateway_url,
                    "tool_name": self._config.refund_tool_name,
                },
            )
        except Exception as exc:
            self._events.appendleft(
                {
                    "status": "gateway_error",
                    "error": str(exc),
                    "trace_id": request.trace_id,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
            if self._config.fallback_to_stub_on_error and self._fallback_adapter is not None:
                return self._fallback_adapter.submit_approval_request(request)
            raise

    def snapshot_state(self) -> dict[str, Any]:
        return {
            "mode": self._config.mode,
            "gateway_url": self._config.gateway_url,
            "refund_tool_name": self._config.refund_tool_name,
            "events": list(self._events),
            "trace_events": list(self._trace_events),
            "tool_registrations": list(self._tool_registrations),
        }

    def _post_mcp(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._config.gateway_url:
            raise ValueError("AgentCore gateway URL is not configured")
        headers = {"Content-Type": "application/json"}
        if self._config.gateway_auth_header:
            headers["Authorization"] = self._config.gateway_auth_header
        timeout = httpx.Timeout(self._config.timeout_seconds)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{self._config.gateway_url.rstrip('/')}/mcp", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
