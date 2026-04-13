from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from internal.modules.orchestration.graph import AssistGraphFactory


@dataclass
class FakeTask:
    id: str
    trace_id: str
    kind: str
    priority: str
    reason: str
    user_input: str
    intent: str
    payload: dict

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "kind": self.kind,
            "priority": self.priority,
            "reason": self.reason,
            "user_input": self.user_input,
            "intent": self.intent,
            "payload": self.payload,
        }


class FakeOperatorTasks:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def enqueue(
        self,
        *,
        trace_id: str,
        kind: str,
        priority: str,
        reason: str,
        user_input: str,
        intent: str,
        payload: dict,
    ) -> FakeTask:
        record = {
            "trace_id": trace_id,
            "kind": kind,
            "priority": priority,
            "reason": reason,
            "user_input": user_input,
            "intent": intent,
            "payload": payload,
        }
        self.calls.append(record)
        return FakeTask(id=f"task-{len(self.calls)}", **record)


class FakeRetrievalRouter:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def retrieve(
        self,
        *,
        query: str,
        provider: str | None = None,
        limit: int = 3,
        knowledge_base_id: str | None = None,
        model_arn_or_id: str | None = None,
    ) -> dict:
        self.calls.append(
            {
                "query": query,
                "provider": provider,
                "limit": limit,
                "knowledge_base_id": knowledge_base_id,
                "model_arn_or_id": model_arn_or_id,
            }
        )
        if provider == "bedrock_knowledge_base":
            return {
                "provider": "bedrock_knowledge_base",
                "items": [],
                "text": "Managed KB answer about returns and policy windows.",
                "citations": [{"source": "kb://policy"}],
                "metadata": {
                    "knowledge_base_id": "kb-demo",
                    "model_arn_or_id": "arn:aws:bedrock:demo-model",
                    "session_id": "session-1",
                },
            }
        return {
            "provider": "qdrant",
            "items": [
                {
                    "id": "snippet-1",
                    "score": 0.98,
                    "text": "Local vector result about shipping, catalog, or returns.",
                    "metadata": {"source": "qdrant-demo"},
                }
            ],
            "text": "",
            "citations": [],
            "metadata": {"collection_name": "knowledge_snippets", "limit": limit},
        }


class FakeGenerationRouter:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def generate(
        self,
        *,
        messages: list[dict],
        provider: str | None = None,
        system_prompts: list[str] | None = None,
        model_id: str | None = None,
        inference_config: dict | None = None,
    ) -> dict:
        self.calls.append(
            {
                "messages": messages,
                "provider": provider,
                "system_prompts": system_prompts or [],
                "model_id": model_id,
                "inference_config": inference_config,
            }
        )
        selected_provider = provider or "openrouter"
        return {
            "provider": selected_provider,
            "model_id": f"{selected_provider}/test-model",
            "text": f"drafted answer via {selected_provider}",
            "metadata": {
                "used_stub": selected_provider == "openrouter",
            },
        }


def make_settings(*, generation_provider: str, bedrock_enabled: bool, knowledge_base_id: str = ""):
    return SimpleNamespace(
        inference=SimpleNamespace(provider=generation_provider),
        bedrock=SimpleNamespace(enabled=bedrock_enabled, knowledge_base_id=knowledge_base_id),
    )


@pytest.mark.parametrize(
    ("name", "settings", "user_input", "expected_retrieval_provider", "expected_generation_provider", "expected_escalated"),
    [
        (
            "qdrant_openrouter",
            make_settings(generation_provider="openrouter", bedrock_enabled=False),
            "Recommend a waterproof bluetooth speaker for travel.",
            "qdrant",
            "openrouter",
            False,
        ),
        (
            "qdrant_bedrock_runtime",
            make_settings(generation_provider="bedrock_runtime", bedrock_enabled=True, knowledge_base_id=""),
            "Where is my order shipment right now?",
            "qdrant",
            "bedrock_runtime",
            False,
        ),
        (
            "bedrock_kb_bedrock_runtime",
            make_settings(generation_provider="bedrock_runtime", bedrock_enabled=True, knowledge_base_id="kb-demo"),
            "Can I return a damaged speaker after 30 days?",
            "bedrock_knowledge_base",
            "bedrock_runtime",
            False,
        ),
        (
            "deterministic_escalation",
            make_settings(generation_provider="bedrock_runtime", bedrock_enabled=True, knowledge_base_id="kb-demo"),
            "I need a refund and compensation for this broken order.",
            "",
            "deterministic",
            True,
        ),
    ],
)
def test_assist_graph_provider_matrix(
    name: str,
    settings,
    user_input: str,
    expected_retrieval_provider: str,
    expected_generation_provider: str,
    expected_escalated: bool,
) -> None:
    retrieval_router = FakeRetrievalRouter()
    generation_router = FakeGenerationRouter()
    operator_tasks = FakeOperatorTasks()

    graph = AssistGraphFactory(
        settings=settings,
        generation_router=generation_router,
        retrieval_router=retrieval_router,
        operator_tasks=operator_tasks,
    ).build()

    result = asyncio.run(graph.ainvoke({"trace_id": f"trace-{name}", "user_input": user_input}))

    assert bool(result.get("escalated", False)) is expected_escalated

    if expected_escalated:
        assert result["selected_model"] == "deterministic/escalation"
        assert result["generation_provider"] == "deterministic"
        assert result["response_text"]
        assert retrieval_router.calls == []
        assert generation_router.calls == []
        assert len(operator_tasks.calls) == 1
        assert result["operator_task"]["kind"] == "support_review"
        return

    assert result["retrieval_provider"] == expected_retrieval_provider
    assert result["generation_provider"] == expected_generation_provider
    assert result["selected_model"] == f"{expected_generation_provider}/test-model"
    assert result["response_text"] == f"drafted answer via {expected_generation_provider}"
    assert len(retrieval_router.calls) == 1
    assert len(generation_router.calls) == 1
    assert operator_tasks.calls == []

    generation_call = generation_router.calls[0]
    assert generation_call["provider"] == expected_generation_provider
    assert user_input in generation_call["messages"][0]["content"]

    if expected_retrieval_provider == "qdrant":
        assert retrieval_router.calls[0]["provider"] == "qdrant"
        assert result["retrieved_context"][0]["id"] == "snippet-1"
    else:
        assert retrieval_router.calls[0]["provider"] == "bedrock_knowledge_base"
        assert result["retrieved_context"][0]["id"] == "bedrock-kb-response"
        assert result["retrieved_context"][0]["citations"] == [{"source": "kb://policy"}]
