"""Non-overridable GEO V4 protocol loaded by the executor."""

import json
from dataclasses import dataclass
from pathlib import Path


REQUIRED_STAGES = (
    "fact_normalization", "company_intelligence", "product_intelligence",
    "intent_intelligence", "persona_intelligence", "trust_intelligence",
    "keyword_intelligence", "geo_report",
)


class ProtocolViolation(RuntimeError):
    """Raised when a caller attempts to bypass the V4 contract."""


@dataclass(frozen=True)
class ExecutionProtocol:
    protocol_version: str = "4.0.0"
    pipeline_id: str = "geo-v4-fixed-pipeline"
    mode: str = "interactive"
    optional_stages: tuple = ("content_strategy",)
    forbidden_stages: tuple = (
        "legacy_pipeline", "unapproved_research", "unapproved_content_generation",
        "unapproved_external_verification",
    )

    def __post_init__(self):
        policy_path = Path(__file__).resolve().parent.parent / "config" / "pipeline_policy.json"
        try:
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProtocolViolation(f"PROTOCOL-005: cannot load pipeline policy: {exc}") from exc
        required = {
            "default_pipeline": "geo-v4-fixed-pipeline", "legacy_enabled": False,
            "allow_dynamic_routing": False, "allow_agent_override": False,
            "allow_unapproved_tools": False, "require_schema_validation": True,
            "require_traceability": True, "fail_closed": True,
        }
        if any(policy.get(key) != value for key, value in required.items()):
            raise ProtocolViolation("PROTOCOL-006: pipeline policy weakens the V4 execution contract")

    @property
    def required_stages(self):
        return REQUIRED_STAGES

    @property
    def rules(self):
        return {
            "single_fact_source": True, "single_positioning_owner": True,
            "single_keyword_owner": True, "single_report_owner": True,
            "no_implicit_inference": True, "no_unverified_claims": True,
            "schema_validation_required": True, "traceability_required": True,
            "fail_closed": True,
        }

    def as_dict(self):
        return {
            "protocol_version": self.protocol_version, "pipeline_id": self.pipeline_id,
            "mode": self.mode, "required_stages": list(self.required_stages),
            "optional_stages": list(self.optional_stages),
            "forbidden_stages": list(self.forbidden_stages), "rules": self.rules,
        }

    def check_agent_permission(self, agent_name):
        from core.agent_contracts import AGENT_CONTRACTS

        if agent_name not in AGENT_CONTRACTS:
            raise ProtocolViolation(f"PROTOCOL-001: unauthorized agent '{agent_name}'")
        return AGENT_CONTRACTS[agent_name]

    def check_stage(self, stage_name, completed):
        if stage_name in self.forbidden_stages:
            raise ProtocolViolation(f"PROTOCOL-002: forbidden stage '{stage_name}'")
        try:
            expected_index = self.required_stages.index(stage_name)
        except ValueError as exc:
            raise ProtocolViolation(f"PROTOCOL-003: unknown required stage '{stage_name}'") from exc
        if tuple(completed) != self.required_stages[:expected_index]:
            raise ProtocolViolation(f"PROTOCOL-004: stage '{stage_name}' is out of fixed order")
