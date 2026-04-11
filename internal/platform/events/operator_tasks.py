from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class OperatorTask:
    id: str
    trace_id: str
    kind: str
    status: str
    priority: str
    reason: str
    user_input: str
    intent: str
    created_at: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InMemoryOperatorTaskQueue:
    def __init__(self) -> None:
        self._items: deque[OperatorTask] = deque()
        self._lock = Lock()

    def enqueue(
        self,
        *,
        trace_id: str,
        kind: str,
        priority: str,
        reason: str,
        user_input: str,
        intent: str,
        payload: dict[str, Any] | None = None,
    ) -> OperatorTask:
        task = OperatorTask(
            id=str(uuid4()),
            trace_id=trace_id,
            kind=kind,
            status="queued",
            priority=priority,
            reason=reason,
            user_input=user_input,
            intent=intent,
            created_at=datetime.now(UTC).isoformat(),
            payload=payload or {},
        )
        with self._lock:
            self._items.appendleft(task)
        return task

    def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._items)[:limit]
        return [item.to_dict() for item in items]
