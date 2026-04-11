from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from internal.modules.orchestration.state import AssistState
from internal.platform.openrouter.client import OpenRouterClient
from internal.platform.qdrant.adapter import QdrantAdapter


class AssistGraphFactory:
    def __init__(self, openrouter: OpenRouterClient, qdrant: QdrantAdapter) -> None:
        self._openrouter = openrouter
        self._qdrant = qdrant

    def build(self):
        builder = StateGraph(AssistState)
        builder.add_node("retrieve_context", self.retrieve_context)
        builder.add_node("draft_answer", self.draft_answer)
        builder.add_edge(START, "retrieve_context")
        builder.add_edge("retrieve_context", "draft_answer")
        builder.add_edge("draft_answer", END)
        return builder.compile()

    def retrieve_context(self, state: AssistState) -> AssistState:
        query = state.get("user_input", "")
        snippets = self._qdrant.retrieve(query=query, limit=3)
        return {
            "retrieved_context": [
                {
                    "id": snippet.id,
                    "score": snippet.score,
                    "text": snippet.text,
                    "metadata": snippet.metadata,
                }
                for snippet in snippets
            ]
        }

    async def draft_answer(self, state: AssistState) -> AssistState:
        context_lines = []
        for item in state.get("retrieved_context", []):
            context_lines.append(f"- {item['text']}")
        context_block = "\n".join(context_lines) if context_lines else "- No retrieved evidence."

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the first scaffold of an e-commerce AI orchestrator. "
                    "Answer briefly, stay grounded in the supplied context, and admit uncertainty."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User request: {state.get('user_input', '')}\n\n"
                    f"Retrieved context:\n{context_block}"
                ),
            },
        ]
        result = await self._openrouter.chat(messages)
        return {
            "response_text": result.content,
            "selected_model": result.model,
            "used_stub": result.used_stub,
        }
