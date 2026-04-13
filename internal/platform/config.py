from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT_DIR / "config" / "profiles"


class AppConfig(BaseModel):
    name: str = "opencode-orchestrator"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000


class InferenceConfig(BaseModel):
    provider: str = "openrouter"
    model: str = "openrouter/free"
    fallback_models: list[str] = Field(default_factory=list)
    timeout_seconds: int = 30
    max_tokens: int = 512
    temperature: float = 0.2
    stub_if_missing_api_key: bool = True


class OpenRouterConfig(BaseModel):
    base_url: str = "https://openrouter.ai/api/v1"
    app_name: str = "opencode-orchestrator"
    site_url: str = "http://localhost:8000"


class QdrantConfig(BaseModel):
    url: str = "http://localhost:6333"
    collection_name: str = "knowledge_snippets"
    vector_size: int = 16
    enabled: bool = True
    bootstrap_demo_data: bool = True


class PostgresConfig(BaseModel):
    dsn: str = "postgresql://app:app@localhost:5432/opencode"


class AgentCoreConfig(BaseModel):
    enabled: bool = False
    mode: str = "external_stub"
    base_url: str = "http://localhost:9001"
    timeout_seconds: int = 5
    fallback_to_stub_on_error: bool = True
    gateway_name: str = "support-gateway"
    policy_name: str = "refund-approval-policy"
    gateway_url: str = ""
    gateway_auth_header: str = ""
    refund_tool_name: str = "RefundTarget___process_refund"
    approval_required_actions: list[str] = Field(default_factory=lambda: ["support.request_refund"])
    blocked_actions: list[str] = Field(default_factory=list)


class AWSConfig(BaseModel):
    region: str = "us-east-1"


class BedrockConfig(BaseModel):
    enabled: bool = False
    runtime_model_id: str = ""
    knowledge_base_id: str = ""
    knowledge_model_id: str = ""
    flow_identifier: str = ""
    flow_alias_identifier: str = ""
    enable_trace: bool = True


class ProfileConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    agentcore: AgentCoreConfig = Field(default_factory=AgentCoreConfig)
    aws: AWSConfig = Field(default_factory=AWSConfig)
    bedrock: BedrockConfig = Field(default_factory=BedrockConfig)


class EnvOverrides(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_profile: str = "dev-openrouter-free"
    app_port: int | None = None
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    openrouter_fallback_models: str | None = None
    openrouter_timeout_seconds: int | None = None
    qdrant_url: str | None = None
    qdrant_collection_name: str | None = None
    postgres_dsn: str | None = None
    agentcore_enabled: bool | None = None
    agentcore_mode: str | None = None
    agentcore_base_url: str | None = None
    agentcore_timeout_seconds: int | None = None
    agentcore_fallback_to_stub_on_error: bool | None = None
    agentcore_gateway_name: str | None = None
    agentcore_policy_name: str | None = None
    agentcore_gateway_url: str | None = None
    agentcore_gateway_auth_header: str | None = None
    agentcore_refund_tool_name: str | None = None
    agentcore_approval_required_actions: str | None = None
    agentcore_blocked_actions: str | None = None
    aws_region: str | None = None
    bedrock_enabled: bool | None = None
    bedrock_runtime_model_id: str | None = None
    bedrock_knowledge_base_id: str | None = None
    bedrock_knowledge_model_id: str | None = None
    bedrock_flow_identifier: str | None = None
    bedrock_flow_alias_identifier: str | None = None
    bedrock_enable_trace: bool | None = None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_profile_config(profile_name: str | None = None) -> ProfileConfig:
    env = EnvOverrides()
    selected_profile = profile_name or env.app_profile
    profile_path = CONFIG_DIR / f"{selected_profile}.yaml"
    raw: dict[str, Any] = {}
    if profile_path.exists():
        raw = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}

    config_data = ProfileConfig().model_dump()
    config_data = _deep_merge(config_data, raw)

    if env.app_port is not None:
        config_data["app"]["port"] = env.app_port
    if env.openrouter_model:
        config_data["inference"]["model"] = env.openrouter_model
    if env.openrouter_fallback_models is not None:
        config_data["inference"]["fallback_models"] = _parse_csv(env.openrouter_fallback_models)
    if env.openrouter_timeout_seconds is not None:
        config_data["inference"]["timeout_seconds"] = env.openrouter_timeout_seconds
    if env.qdrant_url:
        config_data["qdrant"]["url"] = env.qdrant_url
    if env.qdrant_collection_name:
        config_data["qdrant"]["collection_name"] = env.qdrant_collection_name
    if env.postgres_dsn:
        config_data["postgres"]["dsn"] = env.postgres_dsn
    if env.agentcore_enabled is not None:
        config_data["agentcore"]["enabled"] = env.agentcore_enabled
    if env.agentcore_mode:
        config_data["agentcore"]["mode"] = env.agentcore_mode
    if env.agentcore_base_url:
        config_data["agentcore"]["base_url"] = env.agentcore_base_url
    if env.agentcore_timeout_seconds is not None:
        config_data["agentcore"]["timeout_seconds"] = env.agentcore_timeout_seconds
    if env.agentcore_fallback_to_stub_on_error is not None:
        config_data["agentcore"]["fallback_to_stub_on_error"] = env.agentcore_fallback_to_stub_on_error
    if env.agentcore_gateway_name:
        config_data["agentcore"]["gateway_name"] = env.agentcore_gateway_name
    if env.agentcore_policy_name:
        config_data["agentcore"]["policy_name"] = env.agentcore_policy_name
    if env.agentcore_gateway_url is not None:
        config_data["agentcore"]["gateway_url"] = env.agentcore_gateway_url
    if env.agentcore_gateway_auth_header is not None:
        config_data["agentcore"]["gateway_auth_header"] = env.agentcore_gateway_auth_header
    if env.agentcore_refund_tool_name is not None:
        config_data["agentcore"]["refund_tool_name"] = env.agentcore_refund_tool_name
    if env.agentcore_approval_required_actions is not None:
        config_data["agentcore"]["approval_required_actions"] = _parse_csv(env.agentcore_approval_required_actions)
    if env.agentcore_blocked_actions is not None:
        config_data["agentcore"]["blocked_actions"] = _parse_csv(env.agentcore_blocked_actions)
    if env.aws_region:
        config_data["aws"]["region"] = env.aws_region
    if env.bedrock_enabled is not None:
        config_data["bedrock"]["enabled"] = env.bedrock_enabled
    if env.bedrock_runtime_model_id is not None:
        config_data["bedrock"]["runtime_model_id"] = env.bedrock_runtime_model_id
    if env.bedrock_knowledge_base_id is not None:
        config_data["bedrock"]["knowledge_base_id"] = env.bedrock_knowledge_base_id
    if env.bedrock_knowledge_model_id is not None:
        config_data["bedrock"]["knowledge_model_id"] = env.bedrock_knowledge_model_id
    if env.bedrock_flow_identifier is not None:
        config_data["bedrock"]["flow_identifier"] = env.bedrock_flow_identifier
    if env.bedrock_flow_alias_identifier is not None:
        config_data["bedrock"]["flow_alias_identifier"] = env.bedrock_flow_alias_identifier
    if env.bedrock_enable_trace is not None:
        config_data["bedrock"]["enable_trace"] = env.bedrock_enable_trace

    return ProfileConfig.model_validate(config_data)


def get_openrouter_api_key() -> str | None:
    return os.getenv("OPENROUTER_API_KEY")
