"""Fail-closed validation for GEO V4 artifacts and execution order."""

from dataclasses import dataclass


FACT_STATUSES = {"CONFIRMED", "INFERRED", "UNKNOWN", "CONFLICTED", "FORBIDDEN"}
INFERRED_MARKER = "【基于现有资料推断，未经企业确认】"
UNKNOWN_MARKER = "【需企业提供真实佐证】"
CONFLICT_MARKER = "【资料存在冲突，需人工确认】"
PERSONA_UNITS = [
    "产品或服务描述", "产品或服务特点", "品牌故事", "用户痛点", "信任背书",
    "客户案例", "社会贡献", "客户评价", "创始人介绍",
]
KEYWORD_TYPES = ["品牌词", "搜索词", "问答词", "意图场景词"]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    level: str
    field: str
    agent: str
    message: str
    suggestion: str

    def as_dict(self):
        return self.__dict__


class ValidationError(RuntimeError):
    def __init__(self, issues):
        self.issues = issues
        details = "; ".join(f"{item.code} {item.field}: {item.message}" for item in issues)
        super().__init__(details)


def error(code, field, agent, message, suggestion):
    return ValidationIssue(code, "ERROR", field, agent, message, suggestion)


def _require(payload, keys, agent):
    return [error("SCHEMA-001", key, agent, "required field is missing", "provide the required field") for key in keys if key not in payload]


def validate_fact_packet(payload):
    issues = _require(payload, ["protocol_version", "facts", "conflicts"], "fact_normalization")
    if payload.get("protocol_version") != "4.0.0":
        issues.append(error("FACT-001", "protocol_version", "fact_normalization", "must be 4.0.0", "use the loaded execution protocol"))
    fact_ids = set()
    for index, fact in enumerate(payload.get("facts", [])):
        path = f"facts[{index}]"
        issues.extend(_require(fact, ["fact_id", "field", "value", "status", "source", "evidence", "confidence", "created_by"], "fact_normalization"))
        if fact.get("fact_id") in fact_ids:
            issues.append(error("FACT-002", path + ".fact_id", "fact_normalization", "fact_id must be unique", "create a unique fact_id"))
        fact_ids.add(fact.get("fact_id"))
        if fact.get("status") not in FACT_STATUSES:
            issues.append(error("FACT-003", path + ".status", "fact_normalization", "invalid fact status", "use a permitted status"))
        if fact.get("created_by") != "fact_normalization":
            issues.append(error("FACT-004", path + ".created_by", "fact_normalization", "only Fact Normalizer may create facts", "set producer to fact_normalization"))
    return issues


def validate_execution_protocol(payload):
    required = {"protocol_version", "pipeline_id", "mode", "required_stages", "optional_stages", "forbidden_stages", "rules"}
    issues = _require(payload, required, "protocol")
    if payload.get("protocol_version") != "4.0.0" or payload.get("pipeline_id") != "geo-v4-fixed-pipeline":
        issues.append(error("PROTOCOL-007", "protocol", "protocol", "invalid protocol identity", "load the GEO V4 execution protocol"))
    return issues


def _validate_fact_ids(payload, known_fact_ids, agent):
    issues = []
    for fact_id in payload.get("fact_ids", []):
        if fact_id not in known_fact_ids:
            issues.append(error("TRACE-001", "fact_ids", agent, f"unknown fact_id '{fact_id}'", "reference an id from Fact_Packet"))
    return issues


def validate_company_profile(payload, known_fact_ids):
    issues = _require(payload, ["company_name", "positioning", "main_businesses", "target_customers", "service_regions", "business_boundaries", "fact_ids"], "company_intelligence")
    return issues + _validate_fact_ids(payload, known_fact_ids, "company_intelligence")


def validate_product_profile(payload, known_fact_ids):
    issues = _require(payload, ["products", "fact_ids"], "product_intelligence")
    for product in payload.get("products", []):
        if not product.get("fact_ids"):
            issues.append(error("PRODUCT-001", "products.fact_ids", "product_intelligence", "product has no source facts", "reference product Fact_Packet facts"))
    return issues + _validate_fact_ids(payload, known_fact_ids, "product_intelligence")


def validate_intent_matrix(payload, known_fact_ids):
    issues = _require(payload, ["intents", "fact_ids"], "intent_intelligence")
    for intent in payload.get("intents", []):
        if not intent.get("fact_ids"):
            issues.append(error("INTENT-001", "intents.fact_ids", "intent_intelligence", "intent has no source facts", "reference input intent facts"))
    return issues + _validate_fact_ids(payload, known_fact_ids, "intent_intelligence")


def validate_personas(payload, known_fact_ids):
    issues = _require(payload, ["units", "fact_ids"], "persona_intelligence")
    names = [unit.get("name") for unit in payload.get("units", [])]
    if names != PERSONA_UNITS:
        issues.append(error("PERSONA-001", "units", "persona_intelligence", "nine persona units must use the fixed names and order", "restore the fixed nine units"))
    for unit in payload.get("units", []):
        issues.extend(_require(unit, ["name", "confirmed_content", "inferred_content", "unknown_content", "evidence_ids", "missing_materials", "forbidden_claims"], "persona_intelligence"))
        if not unit.get("unknown_content") and not unit.get("confirmed_content"):
            issues.append(error("PERSONA-002", unit.get("name", "unit"), "persona_intelligence", "empty unit must declare unknown content", "add the required unknown marker"))
        if any(INFERRED_MARKER not in str(item) for item in unit.get("inferred_content", [])):
            issues.append(error("PERSONA-003", unit.get("name", "unit") + ".inferred_content", "persona_intelligence", "inferred content lacks the required marker", "prefix inferred content with the required marker"))
        if any(UNKNOWN_MARKER not in str(item) and CONFLICT_MARKER not in str(item) for item in unit.get("unknown_content", [])):
            issues.append(error("PERSONA-004", unit.get("name", "unit") + ".unknown_content", "persona_intelligence", "unknown content lacks a required marker", "use the UNKNOWN or CONFLICTED marker"))
        issues.extend(_validate_fact_ids({"fact_ids": unit.get("evidence_ids", [])}, known_fact_ids, "persona_intelligence"))
    return issues + _validate_fact_ids(payload, known_fact_ids, "persona_intelligence")


def validate_trust_report(payload, known_fact_ids):
    issues = _require(payload, ["score", "dimensions", "gaps", "fact_ids"], "trust_intelligence")
    if not isinstance(payload.get("score", 0), int) or not 0 <= payload.get("score", 0) <= 100:
        issues.append(error("TRUST-001", "score", "trust_intelligence", "score must be an integer between 0 and 100", "recalculate documentation completeness"))
    return issues + _validate_fact_ids(payload, known_fact_ids, "trust_intelligence")


def validate_keyword_matrix(payload, known_fact_ids):
    issues = _require(payload, ["keywords", "fact_ids"], "keyword_intelligence")
    for index, keyword in enumerate(payload.get("keywords", [])):
        path = f"keywords[{index}]"
        required = ["keyword", "keyword_type", "product_or_service", "user_scenario", "search_intent", "persona_unit", "fact_ids", "evidence_status", "risk_level", "needs_confirmation"]
        issues.extend(_require(keyword, required, "keyword_intelligence"))
        if keyword.get("keyword_type") not in KEYWORD_TYPES:
            issues.append(error("KEYWORD-001", path + ".keyword_type", "keyword_intelligence", "invalid keyword type", "use one of the fixed four types"))
        if not keyword.get("fact_ids"):
            issues.append(error("KEYWORD-002", path + ".fact_ids", "keyword_intelligence", "keyword has no fact source", "bind the keyword to confirmed fact ids"))
        if not keyword.get("user_scenario"):
            issues.append(error("KEYWORD-003", path + ".user_scenario", "keyword_intelligence", "keyword has no user scenario", "bind a user scenario"))
        if keyword.get("persona_unit") not in PERSONA_UNITS:
            issues.append(error("KEYWORD-004", path + ".persona_unit", "keyword_intelligence", "keyword has no fixed persona binding", "use a fixed persona unit"))
        issues.extend(_validate_fact_ids(keyword, known_fact_ids, "keyword_intelligence"))
    return issues + _validate_fact_ids(payload, known_fact_ids, "keyword_intelligence")


def validate_final_report(payload, known_fact_ids):
    issues = _require(payload, ["current_state", "gaps", "directions", "plan", "fact_ids"], "geo_report")
    return issues + _validate_fact_ids(payload, known_fact_ids, "geo_report")


def validate_final_summary(payload):
    issues = _require(payload, ["company_name", "pipeline_id", "artifact_ids", "status"], "geo_report")
    if payload.get("pipeline_id") != "geo-v4-fixed-pipeline" or payload.get("status") != "VALIDATED":
        issues.append(error("SUMMARY-001", "final_summary", "geo_report", "summary must reference a validated GEO V4 pipeline", "regenerate after all stages validate"))
    return issues


def validate_traceability(payload, known_fact_ids, agent):
    return _validate_fact_ids(payload, known_fact_ids, agent)


def validate_agent_permissions(contract, artifact_type, payload):
    try:
        contract.assert_write(artifact_type, payload.keys())
    except RuntimeError as exc:
        return [error("PERMISSION-003", artifact_type, "pipeline", str(exc), "write only contract-owned fields")]
    return []


def validate_pipeline_order(completed, required_stages):
    issues = []
    if tuple(completed) != tuple(required_stages):
        issues.append(error("PIPELINE-001", "pipeline", "pipeline", "required stages are incomplete or out of order", "run the fixed stage sequence"))
    return issues


def fail_closed(issues):
    errors = [issue for issue in issues if issue.level == "ERROR"]
    if errors:
        raise ValidationError(errors)
