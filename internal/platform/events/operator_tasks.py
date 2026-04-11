from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


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


class PostgresOperatorTaskQueue:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def ping(self) -> bool:
        try:
            with psycopg.connect(self._dsn, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("select 1")
                    cur.fetchone()
            return True
        except Exception:
            return False

    def init_schema(self) -> None:
        statements = [
            "create table if not exists operator_tasks (id text primary key, trace_id text not null, kind text not null, status text not null, priority text not null, reason text not null, user_input text not null, intent text not null, created_at timestamptz not null, payload jsonb not null default '{}'::jsonb)",
            "create index if not exists idx_operator_tasks_created_at on operator_tasks (created_at desc)",
        ]
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                for statement in statements:
                    cur.execute(statement)

    def enqueue(self, *, trace_id: str, kind: str, priority: str, reason: str, user_input: str, intent: str, payload: dict[str, Any] | None = None) -> OperatorTask:
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
        sql = "insert into operator_tasks (id, trace_id, kind, status, priority, reason, user_input, intent, created_at, payload) values (%(id)s, %(trace_id)s, %(kind)s, %(status)s, %(priority)s, %(reason)s, %(user_input)s, %(intent)s, %(created_at)s::timestamptz, %(payload)s)"
        params = task.to_dict() | {"payload": Jsonb(task.payload)}
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
        return task

    def list_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        sql = "select id, trace_id, kind, status, priority, reason, user_input, intent, created_at, payload from operator_tasks order by created_at desc limit %s"
        with psycopg.connect(self._dsn, autocommit=True, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit,))
                rows = cur.fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "id": row["id"],
                    "trace_id": row["trace_id"],
                    "kind": row["kind"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "reason": row["reason"],
                    "user_input": row["user_input"],
                    "intent": row["intent"],
                    "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
                    "payload": row["payload"],
                }
            )
        return items
