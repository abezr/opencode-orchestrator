from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.responses import Response

from internal.platform.agentcore.boundary import ToolRegistrationRequest
from internal.shared.dependencies import (
    get_agentcore_adapter,
    get_assist_graph,
    get_operator_task_queue,
    get_qdrant_adapter,
    get_settings,
    get_support_action_service,
)


logger = logging.getLogger("opencode.api")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class AssistRequest(BaseModel):
    message: str


class AssistResponse(BaseModel):
    trace_id: str
    answer: str
    model: str
    used_stub: bool
    intent: str
    guardrail_sensitive: bool
    escalated: bool
    escalation_reason: str | None
    operator_task: dict[str, Any] | None
    retrieved_context: list[dict]


class RefundReviewRequest(BaseModel):
    order_id: str
    customer_message: str
    requested_amount: float | None = None


class RefundReviewResponse(BaseModel):
    trace_id: str
    status: str
    action_name: str
    message: str
    governance: dict[str, Any]
    operator_task: dict[str, Any] | None
    approval_submission: dict[str, Any] | None


@asynccontextmanager
async def lifespan(_: FastAPI):
    qdrant = get_qdrant_adapter()
    queue = get_operator_task_queue()
    agentcore = get_agentcore_adapter()
    try:
        qdrant.bootstrap_demo_data()
    except Exception:
        logger.exception("Failed to bootstrap demo data")
    try:
        queue.init_schema()
    except Exception:
        logger.exception("Failed to initialize operator task schema")
    try:
        agentcore.register_tool(
            ToolRegistrationRequest(
                tool_name="support.request_refund",
                description="Submit a refund request that may require approval.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "requested_amount": {"type": ["number", "null"]},
                        "customer_message": {"type": "string"},
                    },
                    "required": ["order_id", "customer_message"],
                },
                metadata={"module": "support", "kind": "approval_sensitive_action"},
            )
        )
    except Exception:
        logger.exception("Failed to register AgentCore tool")
    yield


app = FastAPI(title="opencode-orchestrator", version="0.1.7", lifespan=lifespan)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={"trace_id": trace_id, "method": request.method, "path": request.url.path},
        )
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = trace_id
    logger.info(
        "request_completed",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.get("/healthz")
def healthz() -> dict:
    settings = get_settings()
    qdrant = get_qdrant_adapter()
    queue = get_operator_task_queue()
    return {
        "status": "ok",
        "profile": settings.app.env,
        "postgres_reachable": queue.ping(),
        "qdrant_enabled": settings.qdrant.enabled,
        "qdrant_reachable": qdrant.ping() if settings.qdrant.enabled else False,
        "agentcore_enabled": settings.agentcore.enabled,
        "agentcore_mode": settings.agentcore.mode,
        "agentcore_gateway_name": settings.agentcore.gateway_name,
        "agentcore_policy_name": settings.agentcore.policy_name,
        "model": settings.inference.model,
        "fallback_models": settings.inference.fallback_models,
    }


@app.get("/readyz")
def readyz() -> Response | dict:
    settings = get_settings()
    qdrant = get_qdrant_adapter()
    queue = get_operator_task_queue()
    qdrant_ready = (not settings.qdrant.enabled) or qdrant.ping()
    postgres_ready = queue.ping()
    if not postgres_ready:
        return Response(
            content='{"status":"not_ready","reason":"postgres_unreachable"}',
            media_type="application/json",
            status_code=503,
        )
    if not qdrant_ready:
        return Response(
            content='{"status":"not_ready","reason":"qdrant_unreachable"}',
            media_type="application/json",
            status_code=503,
        )
    get_assist_graph()
    return {
        "status": "ready",
        "mode": "live" if not settings.inference.stub_if_missing_api_key else "live-or-stub",
        "postgres_reachable": postgres_ready,
        "agentcore_enabled": settings.agentcore.enabled,
        "agentcore_mode": settings.agentcore.mode,
        "agentcore_gateway_name": settings.agentcore.gateway_name,
        "agentcore_policy_name": settings.agentcore.policy_name,
        "model": settings.inference.model,
        "fallback_models": settings.inference.fallback_models,
    }


@app.get("/internal/escalations")
def list_escalations(limit: int = 20) -> dict:
    queue = get_operator_task_queue()
    return {"items": queue.list_tasks(limit=limit)}


@app.get("/internal/agentcore")
def agentcore_config() -> dict:
    settings = get_settings()
    adapter = get_agentcore_adapter()
    return {
        "enabled": settings.agentcore.enabled,
        "mode": settings.agentcore.mode,
        "base_url": settings.agentcore.base_url,
        "timeout_seconds": settings.agentcore.timeout_seconds,
        "gateway_name": settings.agentcore.gateway_name,
        "policy_name": settings.agentcore.policy_name,
        "approval_required_actions": settings.agentcore.approval_required_actions,
        "blocked_actions": settings.agentcore.blocked_actions,
        "stub_state": adapter.snapshot_state(),
    }


@app.post("/api/v1/support/refund-review", response_model=RefundReviewResponse)
def refund_review(request: Request, payload: RefundReviewRequest) -> RefundReviewResponse:
    service = get_support_action_service()
    trace_id = request.state.trace_id
    result = service.request_refund_review(
        trace_id=trace_id,
        order_id=payload.order_id,
        customer_message=payload.customer_message,
        requested_amount=payload.requested_amount,
    )
    return RefundReviewResponse(trace_id=trace_id, **result.to_dict())


@app.post("/api/v1/assist", response_model=AssistResponse)
async def assist(request: Request, payload: AssistRequest) -> AssistResponse:
    graph = get_assist_graph()
    trace_id = request.state.trace_id
    result = await graph.ainvoke({"user_input": payload.message, "trace_id": trace_id})
    operator_task = result.get("operator_task") or None
    return AssistResponse(
        trace_id=trace_id,
        answer=result.get("response_text", ""),
        model=result.get("selected_model", "unknown"),
        used_stub=bool(result.get("used_stub", False)),
        intent=result.get("intent", "general"),
        guardrail_sensitive=bool(result.get("guardrail_sensitive", False)),
        escalated=bool(result.get("escalated", False)),
        escalation_reason=result.get("escalation_reason"),
        operator_task=operator_task,
        retrieved_context=result.get("retrieved_context", []),
    )
