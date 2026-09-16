"""Field-level ownership for every V4 pipeline agent."""

from dataclasses import dataclass

from core.execution_protocol import ProtocolViolation


@dataclass(frozen=True)
class AgentContract:
    can_read: tuple
    can_write: tuple
    can_modify: tuple
    cannot_write: tuple

    def assert_write(self, artifact_type, fields):
        if artifact_type not in self.can_write:
            raise ProtocolViolation(f"PERMISSION-001: cannot write '{artifact_type}'")
        unauthorized = set(fields) - set(self.can_modify)
        if unauthorized:
            raise ProtocolViolation(
                f"PERMISSION-002: unauthorized fields for {artifact_type}: {sorted(unauthorized)}"
            )


AGENT_CONTRACTS = {
    "fact_normalization": AgentContract(
        ("raw_input",), ("fact_packet",), ("protocol_version", "facts", "conflicts"),
        ("company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "keyword_matrix", "geo_report"),
    ),
    "company_intelligence": AgentContract(
        ("fact_packet",), ("company_profile",),
        ("company_name", "positioning", "main_businesses", "target_customers", "service_regions", "business_boundaries", "fact_ids"),
        ("fact_packet", "product_profile", "intent_keyword_matrix", "nine_personas", "keyword_matrix", "geo_report"),
    ),
    "product_intelligence": AgentContract(
        ("fact_packet", "company_profile"), ("product_profile",), ("products", "fact_ids"),
        ("fact_packet", "company_profile", "intent_keyword_matrix", "nine_personas", "keyword_matrix", "geo_report"),
    ),
    "intent_intelligence": AgentContract(
        ("fact_packet", "company_profile", "product_profile"), ("intent_keyword_matrix",), ("intents", "fact_ids"),
        ("fact_packet", "company_profile", "product_profile", "nine_personas", "keyword_matrix", "geo_report"),
    ),
    "persona_intelligence": AgentContract(
        ("fact_packet", "company_profile", "product_profile", "intent_keyword_matrix"), ("nine_personas",), ("units", "fact_ids"),
        ("fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "keyword_matrix", "geo_report"),
    ),
    "trust_intelligence": AgentContract(
        ("fact_packet", "company_profile", "product_profile", "nine_personas"), ("trust_report",), ("score", "dimensions", "gaps", "fact_ids"),
        ("fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "keyword_matrix", "geo_report"),
    ),
    "keyword_intelligence": AgentContract(
        ("fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report"), ("keyword_matrix",), ("keywords", "fact_ids"),
        ("fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report", "geo_report"),
    ),
    "geo_report": AgentContract(
        ("fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report", "keyword_matrix"), ("geo_report", "final_summary"), ("current_state", "gaps", "directions", "plan", "fact_ids", "company_name", "pipeline_id", "artifact_ids", "status"),
        ("fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report", "keyword_matrix"),
    ),
}
