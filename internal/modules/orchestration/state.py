from __future__ import annotations

from typing import Any, TypedDict


class AssistState(TypedDict, total=False):
    user_input: str
    retrieved_context: list[dict[str, Any]]
    response_text: str
    selected_model: str
    used_stub: bool
