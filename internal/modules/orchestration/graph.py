from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from internal.modules.orchestration.state import AssistState, Intent
from internal.platform.config import ProfileConfig
from internal.platform.inference.router import GenerationRouter
from internal.platform.retrieval.router import RetrievalRouter


class AssistGraphFactory:
    def __init__(
        self,
        settings: ProfileConfig,
        generation_router: GenerationRouter,
        retrieval_router: RetrievalRouter,
        operator_tasks: Any,
    ) -> None:
        self._settings = settings
        self._generation_router = generation_router
        self._retrieval_router = retrieval_router
        self._operator_tasks = operator_tasks

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
        operator_task = self._operator_tasks.enqueue(
            trace_id=state.get("trace_id", ""),
            kind="support_review",
            priority="high",
            reason=reason,
            user_input=state.get("user_input", ""),
            intent=state.get("intent", "general"),
            payload={
                "guardrail_sensitive": bool(state.get("guardrail_sensitive", False)),
            },
        )
        return {
            "escalated": True,
            "escalation_reason": reason,
            "operator_task": operator_task.to_dict(),
            "response_text": answer,
            "selected_model": "deterministic/escalation",
            "generation_provider": "deterministic",
            "used_stub": False,
            "retrieved_context": [],
        }

    def retrieve_context(self, state: AssistState) -> AssistState:
        query = state.get("user_input", "")
        provider = self._select_retrieval_provider(state)
        result = self._retrieval_router.retrieve(query=query, provider=provider, limit=3)
        retrieved_context: list[dict[str, Any]] = []
        if result["provider"] == "qdrant":
            retrieved_context = list(result.get("items", []))
        else:
            text = result.get("text", "")
            retrieved_context = [
                {
                    "id": "bedrock-kb-response",
                    "score": 1.0,
                    "text": text,
                    "metadata": result.get("metadata", {}),
                    "citations": result.get("citations", []),
                    "provider": result.get("provider"),
                }
            ] if text else []
        return {
            "retrieval_provider": result.get("provider", provider),
            "retrieved_context": retrieved_context,
        }

    async def draft_answer(self, state: AssistState) -> AssistState:
        context_lines: list[str] = []
        for item in state.get("retrieved_context", []):
            text = str(item.get("text", "")).strip()
            if text:
                context_lines.append(f"- {text}")
        context_block = "\n".join(context_lines) if context_lines else "- No retrieved evidence."
        guardrail_note = (
            "Sensitive support flow detected. Be careful and suggest human review if the context is insufficient."
            if state.get("guardrail_sensitive")
            else "No special guardrail flags detected."
        )

        result = await self._generation_router.generate(
            provider=self._settings.inference.provider,
            system_prompts=[
                "You are the first scaffold of an e-commerce AI orchestrator. Answer briefly, stay grounded in the supplied context, and admit uncertainty."
            ],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Intent: {state.get('intent', 'general')}\n"
                        f"Guardrail: {guardrail_note}\n"
                        f"Retrieval provider: {state.get('retrieval_provider', 'qdrant')}\n\n"
                        f"User request: {state.get('user_input', '')}\n\n"
                        f"Retrieved context:\n{context_block}"
                    ),
                }
            ],
        )
        return {
            "escalated": False,
            "escalation_reason": "",
            "operator_task": {},
            "response_text": result.get("text", ""),
            "selected_model": result.get("model_id", "unknown"),
            "generation_provider": result.get("provider", self._settings.inference.provider),
            "used_stub": bool(result.get("metadata", {}).get("used_stub", False)),
        }

    def _select_retrieval_provider(self, state: AssistState) -> str:
        intent = state.get("intent", "general")
        if self._settings.bedrock.enabled and self._settings.bedrock.knowledge_base_id and intent in {"returns", "general"}:
            return "bedrock_knowledge_base"
        return "qdrant"
