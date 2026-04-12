from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from internal.platform.bedrock.flows import BedrockFlowAdapter
from internal.platform.bedrock.knowledge_bases import BedrockKnowledgeBaseAdapter
from internal.platform.bedrock.runtime import BedrockRuntimeAdapter
from internal.platform.config import load_profile_config


class ConverseRequest(BaseModel):
    messages: list[dict] = Field(default_factory=list)
    system_prompts: list[str] = Field(default_factory=list)
    model_id: str | None = None
    inference_config: dict | None = None


class KnowledgeRequest(BaseModel):
    query: str
    knowledge_base_id: str | None = None
    model_arn_or_id: str | None = None


class FlowRequest(BaseModel):
    inputs: list[dict] = Field(default_factory=list)
    flow_identifier: str | None = None
    flow_alias_identifier: str | None = None
    enable_trace: bool | None = None


settings = load_profile_config()
runtime_adapter = BedrockRuntimeAdapter(settings.aws, settings.bedrock)
knowledge_adapter = BedrockKnowledgeBaseAdapter(settings.aws, settings.bedrock)
flow_adapter = BedrockFlowAdapter(settings.aws, settings.bedrock)

app = FastAPI(title="bedrock-demo", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict:
    return {
        "status": "ok",
        "aws_region": settings.aws.region,
        "bedrock_enabled": settings.bedrock.enabled,
        "runtime_model_id": settings.bedrock.runtime_model_id,
        "knowledge_base_id": settings.bedrock.knowledge_base_id,
        "flow_identifier": settings.bedrock.flow_identifier,
        "flow_alias_identifier": settings.bedrock.flow_alias_identifier,
    }


@app.get("/internal/bedrock")
def internal_bedrock() -> dict:
    return {
        "aws_region": settings.aws.region,
        "bedrock": settings.bedrock.model_dump(),
    }


@app.post("/api/v1/bedrock/converse")
def converse(request: ConverseRequest) -> dict:
    return runtime_adapter.converse(
        messages=request.messages,
        system_prompts=request.system_prompts,
        model_id=request.model_id,
        inference_config=request.inference_config,
    )


@app.post("/api/v1/bedrock/knowledge/query")
def knowledge_query(request: KnowledgeRequest) -> dict:
    return knowledge_adapter.retrieve_and_generate(
        query=request.query,
        knowledge_base_id=request.knowledge_base_id,
        model_arn_or_id=request.model_arn_or_id,
    )


@app.post("/api/v1/bedrock/flow/invoke")
def invoke_flow(request: FlowRequest) -> dict:
    return flow_adapter.invoke_flow(
        inputs=request.inputs,
        flow_identifier=request.flow_identifier,
        flow_alias_identifier=request.flow_alias_identifier,
        enable_trace=request.enable_trace,
    )
