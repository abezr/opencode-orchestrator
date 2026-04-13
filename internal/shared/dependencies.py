from __future__ import annotations

from functools import lru_cache

from internal.modules.orchestration.graph import AssistGraphFactory
from internal.modules.support.actions import SupportActionService
from internal.platform.agentcore.external_stub import ExternalAgentCoreAdapterStub
from internal.platform.agentcore.http_client import AgentCoreHttpClientAdapter
from internal.platform.bedrock.flows import BedrockFlowAdapter
from internal.platform.bedrock.knowledge_bases import BedrockKnowledgeBaseAdapter
from internal.platform.bedrock.runtime import BedrockRuntimeAdapter
from internal.platform.config import ProfileConfig, load_profile_config
from internal.platform.events.operator_tasks import PostgresOperatorTaskQueue
from internal.platform.inference.router import GenerationRouter
from internal.platform.openrouter.client import OpenRouterClient
from internal.platform.qdrant.adapter import QdrantAdapter
from internal.platform.retrieval.router import RetrievalRouter


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
def get_bedrock_runtime_adapter() -> BedrockRuntimeAdapter:
    settings = get_settings()
    return BedrockRuntimeAdapter(settings.aws, settings.bedrock)


@lru_cache(maxsize=1)
def get_bedrock_knowledge_base_adapter() -> BedrockKnowledgeBaseAdapter:
    settings = get_settings()
    return BedrockKnowledgeBaseAdapter(settings.aws, settings.bedrock)


@lru_cache(maxsize=1)
def get_bedrock_flow_adapter() -> BedrockFlowAdapter:
    settings = get_settings()
    return BedrockFlowAdapter(settings.aws, settings.bedrock)


@lru_cache(maxsize=1)
def get_operator_task_queue() -> PostgresOperatorTaskQueue:
    settings = get_settings()
    queue = PostgresOperatorTaskQueue(settings.postgres.dsn)
    queue.init_schema()
    return queue


@lru_cache(maxsize=1)
def get_agentcore_adapter():
    settings = get_settings()
    stub = ExternalAgentCoreAdapterStub(settings.agentcore, get_operator_task_queue())
    if settings.agentcore.mode == "http_client":
        fallback = stub if settings.agentcore.fallback_to_stub_on_error else None
        return AgentCoreHttpClientAdapter(settings.agentcore, fallback_adapter=fallback)
    return stub


@lru_cache(maxsize=1)
def get_support_action_service() -> SupportActionService:
    return SupportActionService(agentcore=get_agentcore_adapter())


@lru_cache(maxsize=1)
def get_generation_router() -> GenerationRouter:
    return GenerationRouter(
        settings=get_settings(),
        openrouter=get_openrouter_client(),
        bedrock_runtime=get_bedrock_runtime_adapter(),
    )


@lru_cache(maxsize=1)
def get_retrieval_router() -> RetrievalRouter:
    return RetrievalRouter(
        settings=get_settings(),
        qdrant=get_qdrant_adapter(),
        knowledge_base=get_bedrock_knowledge_base_adapter(),
    )


@lru_cache(maxsize=1)
def get_assist_graph():
    return AssistGraphFactory(
        settings=get_settings(),
        generation_router=get_generation_router(),
        retrieval_router=get_retrieval_router(),
        operator_tasks=get_operator_task_queue(),
    ).build()
