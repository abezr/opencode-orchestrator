from __future__ import annotations

from functools import lru_cache

from internal.modules.orchestration.graph import AssistGraphFactory
from internal.platform.config import ProfileConfig, load_profile_config
from internal.platform.events.operator_tasks import PostgresOperatorTaskQueue
from internal.platform.openrouter.client import OpenRouterClient
from internal.platform.qdrant.adapter import QdrantAdapter


@lru_cache(maxsize=1)
def get_settings() -> ProfileConfig:
    return load_profile_config()


@lru_cache(maxsize=1)
def get_qdrant_adapter() -> QdrantAdapter:
    settings = get_settings()
    adapter = QdrantAdapter(settings.qdrant)
    if settings.qdrant.enabled:
        try:
            adapter.bootstrap_demo_data()
        except Exception:
            pass
    return adapter


@lru_cache(maxsize=1)
def get_openrouter_client() -> OpenRouterClient:
    settings = get_settings()
    return OpenRouterClient(settings.openrouter, settings.inference)


@lru_cache(maxsize=1)
def get_operator_task_queue() -> PostgresOperatorTaskQueue:
    settings = get_settings()
    queue = PostgresOperatorTaskQueue(settings.postgres.dsn)
    queue.init_schema()
    return queue


@lru_cache(maxsize=1)
def get_assist_graph():
    return AssistGraphFactory(
        openrouter=get_openrouter_client(),
        qdrant=get_qdrant_adapter(),
        operator_tasks=get_operator_task_queue(),
    ).build()
