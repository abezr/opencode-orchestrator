from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from internal.shared.dependencies import get_assist_graph, get_qdrant_adapter, get_settings


class AssistRequest(BaseModel):
    message: str


class AssistResponse(BaseModel):
    answer: str
    model: str
    used_stub: bool
    retrieved_context: list[dict]


@asynccontextmanager
async def lifespan(_: FastAPI):
    qdrant = get_qdrant_adapter()
    try:
        qdrant.bootstrap_demo_data()
    except Exception:
        pass
    yield


app = FastAPI(title="opencode-orchestrator", version="0.1.0", lifespan=lifespan)


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
    }


@app.post("/api/v1/assist", response_model=AssistResponse)
async def assist(request: AssistRequest) -> AssistResponse:
    graph = get_assist_graph()
    result = await graph.ainvoke({"user_input": request.message})
    return AssistResponse(
        answer=result.get("response_text", ""),
        model=result.get("selected_model", "unknown"),
        used_stub=bool(result.get("used_stub", False)),
        retrieved_context=result.get("retrieved_context", []),
    )
