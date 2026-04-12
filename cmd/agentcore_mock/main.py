from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field


class EvaluateActionRequest(BaseModel):
    action_name: str
    trace_id: str
    intent: str
    user_input: str
    payload: dict[str, Any] = Field(default_factory=dict)


class RegisterToolRequest(BaseModel):
    tool_name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceEventRequest(BaseModel):
    trace_id: str
    event_name: str
    level: str = "info"
    payload: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    trace_id: str
    action_name: str
    reason: str
    user_input: str
    intent: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: str = "high"


app = FastAPI(title="agentcore-mock", version="0.1.0")

_registered_tools: dict[str, dict[str, Any]] = {}
_trace_events: deque[dict[str, Any]] = deque(maxlen=200)
_approval_submissions: deque[dict[str, Any]] = deque(maxlen=200)
_approval_required_actions = {"support.request_refund", "support.issue_compensation"}
_blocked_actions: set[str] = set()
_gateway_name = "support-gateway"
_policy_name = "refund-approval-policy"


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "gateway_name": _gateway_name,
        "policy_name": _policy_name,
        "approval_required_actions": sorted(_approval_required_actions),
        "blocked_actions": sorted(_blocked_actions),
    }


@app.get("/internal/state")
def internal_state() -> dict[str, Any]:
    return {
        "registered_tools": list(_registered_tools.values()),
        "trace_events": list(_trace_events),
        "approval_submissions": list(_approval_submissions),
    }


@app.post("/gateway/register-tool")
def register_tool(request: RegisterToolRequest) -> dict[str, Any]:
    status = "registered"
    if request.tool_name in _registered_tools:
        status = "already_registered"
    _registered_tools[request.tool_name] = {
        "tool_name": request.tool_name,
        "description": request.description,
        "input_schema": request.input_schema,
        "metadata": request.metadata,
        "gateway_name": _gateway_name,
        "registered_at": datetime.now(UTC).isoformat(),
    }
    return {
        "tool_name": request.tool_name,
        "status": status,
        "gateway_name": _gateway_name,
        "metadata": {"service": "agentcore-mock"},
    }


@app.post("/gateway/evaluate-action")
def evaluate_action(request: EvaluateActionRequest) -> dict[str, Any]:
    if request.action_name in _blocked_actions:
        status = "blocked"
        reason = f"Mock AgentCore blocked '{request.action_name}'."
    elif request.action_name in _approval_required_actions:
        status = "approval_required"
        reason = f"Mock AgentCore requires approval for '{request.action_name}'."
    else:
        status = "allowed"
        reason = f"Mock AgentCore allows '{request.action_name}'."
    return {
        "status": status,
        "reason": reason,
        "gateway_name": _gateway_name,
        "policy_name": _policy_name,
        "metadata": {
            "service": "agentcore-mock",
            "trace_id": request.trace_id,
        },
    }


@app.post("/observability/trace-events")
def emit_trace_event(request: TraceEventRequest) -> dict[str, Any]:
    _trace_events.appendleft(
        {
            "trace_id": request.trace_id,
            "event_name": request.event_name,
            "level": request.level,
            "payload": request.payload,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    return {
        "accepted": True,
        "trace_id": request.trace_id,
        "event_name": request.event_name,
        "metadata": {"service": "agentcore-mock"},
    }


@app.post("/approvals/submit")
def submit_approval_request(request: ApprovalRequest) -> dict[str, Any]:
    approval_id = str(uuid4())
    operator_task = {
        "id": str(uuid4()),
        "trace_id": request.trace_id,
        "kind": "approval_required_support_action",
        "status": "queued",
        "priority": request.priority,
        "reason": request.reason,
        "user_input": request.user_input,
        "intent": request.intent,
        "created_at": datetime.now(UTC).isoformat(),
        "payload": {
            "approval_id": approval_id,
            "action_name": request.action_name,
            **request.payload,
        },
    }
    _approval_submissions.appendleft(
        {
            "approval_id": approval_id,
            "trace_id": request.trace_id,
            "action_name": request.action_name,
            "status": "submitted",
            "created_at": datetime.now(UTC).isoformat(),
            "operator_task": operator_task,
        }
    )
    return {
        "status": "submitted",
        "approval_id": approval_id,
        "gateway_name": _gateway_name,
        "policy_name": _policy_name,
        "operator_task": operator_task,
        "metadata": {"service": "agentcore-mock"},
    }
