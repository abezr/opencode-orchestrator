from __future__ import annotations

from fastapi.testclient import TestClient

from cmd.api.main import app, provide_assist_graph


class FakeGraph:
    async def ainvoke(self, state: dict) -> dict:
        return {
            "response_text": f"HTTP test answer for: {state['user_input']}",
            "selected_model": "openrouter/test-http-model",
            "used_stub": True,
            "intent": "general",
            "guardrail_sensitive": False,
            "escalated": False,
            "escalation_reason": "",
            "operator_task": {},
            "retrieved_context": [
                {
                    "id": "http-test-snippet",
                    "score": 0.99,
                    "text": "HTTP-level retrieval snippet.",
                    "metadata": {"source": "test"},
                }
            ],
        }


def test_post_assist_returns_http_response_with_dependency_override() -> None:
    app.dependency_overrides[provide_assist_graph] = lambda: FakeGraph()
    try:
        client = TestClient(app)
        response = client.post("/api/v1/assist", json={"message": "hello from http test"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "HTTP test answer for: hello from http test"
    assert body["model"] == "openrouter/test-http-model"
    assert body["used_stub"] is True
    assert body["intent"] == "general"
    assert body["guardrail_sensitive"] is False
    assert body["escalated"] is False
    assert body["retrieved_context"][0]["id"] == "http-test-snippet"
    assert response.headers["X-Request-ID"]
