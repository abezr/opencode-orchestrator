from __future__ import annotations

from typing import Any, Literal, TypedDict


Intent = Literal["returns", "orders", "catalog", "general"]


class AssistState(TypedDict, total=False):
    trace_id: str
    user_input: str
    guardrail_sensitive: bool
    intent: Intent
    escalated: bool
    escalation_reason: str
    retrieved_context: list[dict[str, Any]]
    response_text: str
    selected_model: str
    used_stub: bool
