from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from internal.modules.orchestration.state import AssistState, Intent
from internal.platform.openrouter.client import OpenRouterClient
from internal.platform.qdrant.adapter import QdrantAdapter


class AssistGraphFactory:
    def __init__(self, openrouter: OpenRouterClient, qdrant: QdrantAdapter) -> None:
        self._openrouter = openrouter
        self._qdrant = qdrant

    def build(self):
        builder = StateGraph(AssistState)
        builder.add_node("guardrail_check", self.guardrail_check)
        builder.add_node("classify_intent", self.classify_intent)
        builder.add_node("deterministic_escalation", self.deterministic_escalation)
        builder.add_node("retrieve_context", self.retrieve_context)
        builder.add_node("draft_answer", self.draft_answer)
        builder.add_edge(START, "guardrail_check")
        builder.add_edge("guardrail_check", "classify_intent")
        builder.add_conditional_edges(
            "classify_intent",
            self.route_after_classification,
            {
                "deterministic_escalation": "deterministic_escalation",
                "retrieve_context": "retrieve_context",
            },
        )
        builder.add_edge("deterministic_escalation", END)
        builder.add_edge("retrieve_context", "draft_answer")
        builder.add_edge("draft_answer", END)
        return builder.compile()

    def guardrail_check(self, state: AssistState) -> AssistState:
        text = state.get("user_input", "").lower()
        sensitive_markers = ["refund", "compensation", "payment issue"]
        return {"guardrail_sensitive": any(marker in text for marker in sensitive_markers)}

    def classify_intent(self, state: AssistState) -> AssistState:
        text = state.get("user_input", "").lower()
        intent: Intent = "general"
        if any(keyword in text for keyword in ["return", "refund", "exchange"]):
            intent = "returns"
        elif any(keyword in text for keyword in ["order", "shipment", "tracking", "delivered"]):
            intent = "orders"
        elif any(keyword in text for keyword in ["speaker", "product", "recommend", "bluetooth", "waterproof"]):
            intent = "catalog"
        return {"intent": intent}

    def route_after_classification(self, state: AssistState) -> str:
        if state.get("guardrail_sensitive"):
            return "deterministic_escalation"
        return "retrieve_context"

    def deterministic_escalation(self, state: AssistState) -> AssistState:
        reason = "Sensitive support flow detected; routing to human review instead of autonomous generation."
        answer = "Your request needs human review before I can answer safely. I’m escalating it to a support specialist now."
        return {
            "escalated": True,
            "escalation_reason": reason,
            "response_text": answer,
            "selected_model": "deterministic/escalation",
            "used_stub": False,
            "retrieved_context": [],
        }

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
        guardrail_note = (
            "Sensitive support flow detected. Be careful and suggest human review if the context is insufficient."
            if state.get("guardrail_sensitive")
            else "No special guardrail flags detected."
        )

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
                    f"Intent: {state.get('intent', 'general')}\n"
                    f"Guardrail: {guardrail_note}\n\n"
                    f"User request: {state.get('user_input', '')}\n\n"
                    f"Retrieved context:\n{context_block}"
                ),
            },
        ]
        result = await self._openrouter.chat(messages)
        return {
            "escalated": False,
            "escalation_reason": "",
            "response_text": result.content,
            "selected_model": result.model,
            "used_stub": result.used_stub,
        }
