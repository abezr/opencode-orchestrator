from __future__ import annotations

from typing import Any

import boto3

from internal.platform.config import AWSConfig, BedrockConfig


class BedrockFlowAdapter:
    def __init__(self, aws: AWSConfig, bedrock: BedrockConfig) -> None:
        self._aws = aws
        self._bedrock = bedrock
        self._client = boto3.client("bedrock-agent-runtime", region_name=aws.region)

    def invoke_flow(
        self,
        *,
        inputs: list[dict[str, Any]],
        flow_identifier: str | None = None,
        flow_alias_identifier: str | None = None,
        enable_trace: bool | None = None,
    ) -> dict[str, Any]:
        selected_flow = flow_identifier or self._bedrock.flow_identifier
        selected_alias = flow_alias_identifier or self._bedrock.flow_alias_identifier
        if not selected_flow:
            raise ValueError("Bedrock flow identifier is not configured")
        if not selected_alias:
            raise ValueError("Bedrock flow alias identifier is not configured")

        response = self._client.invoke_flow(
            flowIdentifier=selected_flow,
            flowAliasIdentifier=selected_alias,
            enableTrace=self._bedrock.enable_trace if enable_trace is None else enable_trace,
            inputs=inputs,
        )

        outputs: list[dict[str, Any]] = []
        traces: list[dict[str, Any]] = []
        events = response.get("responseStream") or response.get("eventStream") or []
        for event in events:
            if "flowOutputEvent" in event:
                outputs.append(event["flowOutputEvent"])
            elif "flowTraceEvent" in event:
                traces.append(event["flowTraceEvent"])

        return {
            "flow_identifier": selected_flow,
            "flow_alias_identifier": selected_alias,
            "outputs": outputs,
            "traces": traces,
        }
