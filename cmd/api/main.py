from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.responses import Response

from internal.shared.dependencies import get_assist_graph, get_qdrant_adapter, get_settings


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
    retrieved_context: list[dict]


@asynccontextmanager
async def lifespan(_: FastAPI):
    qdrant = get_qdrant_adapter()
    try:
        qdrant.bootstrap_demo_data()
    except Exception:
        logger.exception("Failed to bootstrap demo data")
    yield


app = FastAPI(title="opencode-orchestrator", version="0.1.2", lifespan=lifespan)


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
    return {
        "status": "ok",
        "profile": settings.app.env,
        "qdrant_enabled": settings.qdrant.enabled,
        "qdrant_reachable": qdrant.ping() if settings.qdrant.enabled else False,
        "model": settings.inference.model,
        "fallback_models": settings.inference.fallback_models,
    }


@app.get("/readyz")
def readyz() -> Response | dict:
    settings = get_settings()
    qdrant = get_qdrant_adapter()
    qdrant_ready = (not settings.qdrant.enabled) or qdrant.ping()
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
        "model": settings.inference.model,
        "fallback_models": settings.inference.fallback_models,
    }


@app.post("/api/v1/assist", response_model=AssistResponse)
async def assist(request: Request, payload: AssistRequest) -> AssistResponse:
    graph = get_assist_graph()
    trace_id = request.state.trace_id
    result = await graph.ainvoke({"user_input": payload.message, "trace_id": trace_id})
    return AssistResponse(
        trace_id=trace_id,
        answer=result.get("response_text", ""),
        model=result.get("selected_model", "unknown"),
        used_stub=bool(result.get("used_stub", False)),
        intent=result.get("intent", "general"),
        guardrail_sensitive=bool(result.get("guardrail_sensitive", False)),
        escalated=bool(result.get("escalated", False)),
        escalation_reason=result.get("escalation_reason"),
        retrieved_context=result.get("retrieved_context", []),
    )
