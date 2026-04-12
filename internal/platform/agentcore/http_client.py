from __future__ import annotations

from collections import deque
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, Callable, TypeVar

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

T = TypeVar("T")


class AgentCoreHttpClientAdapter:
    def __init__(
        self,
        config: AgentCoreConfig,
        fallback_adapter: AgentCoreGatewayPolicyAdapter | None = None,
    ) -> None:
        self._config = config
        self._fallback_adapter = fallback_adapter
        self._transport_events: deque[dict[str, Any]] = deque(maxlen=200)
        self._fallback_count = 0

    def evaluate_action(self, request: GatewayPolicyRequest) -> GatewayPolicyDecision:
        return self._call_with_fallback(
            operation="evaluate_action",
            request_payload=asdict(request),
            transport_call=lambda: self._evaluate_action_http(request),
            fallback_call=lambda: self._fallback_adapter.evaluate_action(request) if self._fallback_adapter else None,
        )

    def register_tool(self, request: ToolRegistrationRequest) -> ToolRegistrationResult:
        return self._call_with_fallback(
            operation="register_tool",
            request_payload=asdict(request),
            transport_call=lambda: self._register_tool_http(request),
            fallback_call=lambda: self._fallback_adapter.register_tool(request) if self._fallback_adapter else None,
        )

    def emit_trace_event(self, request: TraceEventRequest) -> TraceEventResult:
        return self._call_with_fallback(
            operation="emit_trace_event",
            request_payload=asdict(request),
            transport_call=lambda: self._emit_trace_event_http(request),
            fallback_call=lambda: self._fallback_adapter.emit_trace_event(request) if self._fallback_adapter else None,
        )

    def submit_approval_request(self, request: ApprovalRequest) -> ApprovalSubmissionResult:
        return self._call_with_fallback(
            operation="submit_approval_request",
            request_payload=asdict(request),
            transport_call=lambda: self._submit_approval_request_http(request),
            fallback_call=lambda: self._fallback_adapter.submit_approval_request(request) if self._fallback_adapter else None,
        )

    def snapshot_state(self) -> dict[str, Any]:
        return {
            "integration_mode": self._config.mode,
            "base_url": self._config.base_url,
            "timeout_seconds": self._config.timeout_seconds,
            "fallback_to_stub_on_error": self._config.fallback_to_stub_on_error,
            "fallback_count": self._fallback_count,
            "transport_events": list(self._transport_events),
        }

    def _call_with_fallback(
        self,
        *,
        operation: str,
        request_payload: dict[str, Any],
        transport_call: Callable[[], T],
        fallback_call: Callable[[], T | None],
    ) -> T:
        try:
            result = transport_call()
            self._record_event(operation=operation, status="http_success", request_payload=request_payload)
            return result
        except Exception as exc:
            self._record_event(
                operation=operation,
                status="http_error",
                request_payload=request_payload,
                error=str(exc),
            )
            if self._config.fallback_to_stub_on_error:
                fallback_result = fallback_call()
                if fallback_result is not None:
                    self._fallback_count += 1
                    self._record_event(operation=operation, status="fallback_used", request_payload=request_payload)
                    return fallback_result
            raise

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        timeout = httpx.Timeout(self._config.timeout_seconds)
        with httpx.Client(base_url=self._config.base_url, timeout=timeout) as client:
            response = client.post(path, json=payload)
            response.raise_for_status()
            return response.json()

    def _evaluate_action_http(self, request: GatewayPolicyRequest) -> GatewayPolicyDecision:
        data = self._post("/gateway/evaluate-action", asdict(request))
        return GatewayPolicyDecision(
            status=data["status"],
            reason=data["reason"],
            gateway_name=data.get("gateway_name", self._config.gateway_name),
            policy_name=data.get("policy_name", self._config.policy_name),
            metadata=data.get("metadata", {}),
        )

    def _register_tool_http(self, request: ToolRegistrationRequest) -> ToolRegistrationResult:
        data = self._post("/gateway/register-tool", asdict(request))
        return ToolRegistrationResult(
            tool_name=data.get("tool_name", request.tool_name),
            status=data.get("status", "registered"),
            gateway_name=data.get("gateway_name", self._config.gateway_name),
            metadata=data.get("metadata", {}),
        )

    def _emit_trace_event_http(self, request: TraceEventRequest) -> TraceEventResult:
        data = self._post("/observability/trace-events", asdict(request))
        return TraceEventResult(
            accepted=bool(data.get("accepted", True)),
            trace_id=data.get("trace_id", request.trace_id),
            event_name=data.get("event_name", request.event_name),
            metadata=data.get("metadata", {}),
        )

    def _submit_approval_request_http(self, request: ApprovalRequest) -> ApprovalSubmissionResult:
        data = self._post("/approvals/submit", asdict(request))
        return ApprovalSubmissionResult(
            status=data.get("status", "submitted"),
            approval_id=data["approval_id"],
            gateway_name=data.get("gateway_name", self._config.gateway_name),
            policy_name=data.get("policy_name", self._config.policy_name),
            operator_task=data.get("operator_task"),
            metadata=data.get("metadata", {}),
        )

    def _record_event(
        self,
        *,
        operation: str,
        status: str,
        request_payload: dict[str, Any],
        error: str | None = None,
    ) -> None:
        self._transport_events.appendleft(
            {
                "operation": operation,
                "status": status,
                "request_payload": request_payload,
                "error": error,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
