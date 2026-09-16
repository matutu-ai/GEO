"""GEO V4 fixed, validated, traceable pipeline."""

from copy import deepcopy

from core.agent_contracts import AGENT_CONTRACTS
from core.artifact_store import ArtifactStore
from core.execution_protocol import ExecutionProtocol, ProtocolViolation
from validators.v4_validator import (
    KEYWORD_TYPES, PERSONA_UNITS, ValidationError, fail_closed, validate_agent_permissions,
    validate_company_profile, validate_fact_packet, validate_final_report, validate_intent_matrix,
    validate_keyword_matrix, validate_personas, validate_pipeline_order, validate_product_profile,
    validate_trust_report, validate_execution_protocol, validate_final_summary,
)


MISSING = "【需企业提供真实佐证】"
INFERRED = "【基于现有资料推断，未经企业确认】"
CONFLICTED = "【资料存在冲突，需人工确认】"
FACT_FIELDS = (
    "company_name", "official_website", "positioning", "main_businesses", "target_customers",
    "service_regions", "core_capabilities", "use_cases", "competitive_advantages",
    "business_boundaries", "products", "user_intents", "user_pain_points", "brand_story",
    "development_history", "evidence", "founder", "social_contributions",
    "environmental_contributions", "local_contributions", "public_welfare_actions",
)
FAST_PATH_REQUIRED = ("company_name", "positioning", "main_businesses", "target_customers", "products")


class PipelineBlocked(RuntimeError):
    pass


def _present(value):
    return value is not None and (not isinstance(value, str) or bool(value.strip())) and value != [] and value != {}


def _display(fact):
    if fact["status"] == "UNKNOWN":
        return MISSING
    if fact["status"] == "INFERRED":
        return INFERRED
    if fact["status"] == "CONFLICTED":
        return CONFLICTED
    if fact["status"] == "FORBIDDEN":
        return "【禁止输出】"
    value = fact["value"]
    if isinstance(value, list):
        return "；".join(str(item) for item in value)
    return str(value)


class FixedPipeline:
    def __init__(self, mode="interactive"):
        if mode not in {"interactive", "fast_path"}:
            raise PipelineBlocked("INPUT-001: mode must be interactive or fast_path")
        self.protocol = ExecutionProtocol(mode=mode)
        try:
            fail_closed(validate_execution_protocol(self.protocol.as_dict()))
        except ValidationError as exc:
            raise PipelineBlocked(f"VALIDATION_BLOCKED: {exc}") from exc
        self.store = ArtifactStore()
        self.completed = []
        self.trace = {"protocol": self.protocol.as_dict(), "stages": [], "artifacts": [], "issues": []}

    def normalize(self, raw_input):
        self.protocol.check_stage("fact_normalization", self.completed)
        self.protocol.check_agent_permission("fact_normalization")
        if not isinstance(raw_input, dict) or not _present(raw_input.get("company_name")):
            raise PipelineBlocked("INPUT-002: company_name is required")
        conflicts = raw_input.get("conflicts", {})
        if not isinstance(conflicts, dict):
            raise PipelineBlocked("INPUT-003: conflicts must be an object keyed by field")
        facts = []
        for index, field in enumerate(FACT_FIELDS, start=1):
            if field in conflicts:
                value, status = deepcopy(conflicts[field]), "CONFLICTED"
            elif _present(raw_input.get(field)):
                value, status = deepcopy(raw_input[field]), "CONFIRMED"
            else:
                value, status = None, "UNKNOWN"
            facts.append({
                "fact_id": f"fact-{index:03d}", "field": field, "value": value, "status": status,
                "source": f"input.{field}", "evidence": [], "confidence": "high" if status == "CONFIRMED" else "low",
                "created_by": "fact_normalization",
            })
        payload = {"protocol_version": "4.0.0", "facts": facts, "conflicts": [{"field": field, "values": values} for field, values in conflicts.items()]}
        self._store_validated("fact_normalization", "fact_packet", "schemas/fact-packet-v4.schema.json", payload, [])
        return self.store.get("fact_packet")["payload"]

    def interactive_state(self, raw_input):
        fact_packet = self.normalize(raw_input)
        facts = {fact["field"]: fact for fact in fact_packet["facts"]}
        missing = [field for field in FAST_PATH_REQUIRED if facts[field]["status"] != "CONFIRMED"]
        conflicts = [item["field"] for item in fact_packet["conflicts"]]
        return {
            "current_stage": "fact_normalization", "confirmed_facts": ["company_name"],
            "analysis": "已创建唯一 Fact_Packet；资料不足时不得进入企业画像、关键词或最终报告。",
            "missing_materials": missing, "conflicts": conflicts,
            "next_action": "补充企业定位、主营业务、目标客户和产品资料，或明确要求 Fast Path。",
        }

    def run(self, raw_input):
        fact_packet = self.normalize(raw_input)
        fact_map = {fact["field"]: fact for fact in fact_packet["facts"]}
        if any(fact_map[field]["status"] != "CONFIRMED" for field in FAST_PATH_REQUIRED):
            raise PipelineBlocked("INPUT-004: Fast Path requires confirmed positioning, main_businesses, target_customers, and products; use Interactive Mode to collect missing materials")
        self._run_company(fact_map)
        self._run_products(fact_map)
        self._run_intents(fact_map)
        self._run_personas(fact_map)
        self._run_trust(fact_map)
        self._run_keywords(fact_map)
        self._run_report(fact_map)
        issues = validate_pipeline_order(self.completed, self.protocol.required_stages)
        self._fail(issues)
        self.trace["artifacts"] = self.store.all()
        return self.store.all(), self.trace

    def _fact_value(self, fact):
        return {"value": deepcopy(fact["value"]), "status": fact["status"], "fact_id": fact["fact_id"], "display": _display(fact)}

    def _run_company(self, facts):
        payload = {
            "company_name": self._fact_value(facts["company_name"]), "positioning": self._fact_value(facts["positioning"]),
            "main_businesses": self._fact_value(facts["main_businesses"]), "target_customers": self._fact_value(facts["target_customers"]),
            "service_regions": self._fact_value(facts["service_regions"]), "business_boundaries": self._fact_value(facts["business_boundaries"]),
            "fact_ids": [facts[key]["fact_id"] for key in ("company_name", "positioning", "main_businesses", "target_customers", "service_regions", "business_boundaries")],
        }
        self._store_validated("company_intelligence", "company_profile", "schemas/company-profile-v4.schema.json", payload, ["fact_packet"])

    def _run_products(self, facts):
        products = []
        source = facts["products"]
        if source["status"] == "CONFIRMED" and isinstance(source["value"], list):
            for item in source["value"]:
                if not isinstance(item, dict):
                    continue
                products.append({
                    "name": item.get("name", MISSING), "category": item.get("category", MISSING),
                    "target_customers": item.get("target_customers", MISSING), "use_cases": item.get("use_cases", MISSING),
                    "problems_solved": item.get("problems_solved", MISSING), "advantages": item.get("advantages", MISSING),
                    "technical_features": item.get("technical_features", MISSING), "delivery_methods": item.get("delivery_methods", MISSING),
                    "boundaries": item.get("boundaries", MISSING), "fact_ids": [source["fact_id"]],
                })
        payload = {"products": products, "fact_ids": [source["fact_id"]]}
        self._store_validated("product_intelligence", "product_profile", "schemas/product-profile-v4.schema.json", payload, ["fact_packet", "company_profile"])

    def _run_intents(self, facts):
        source = facts["user_intents"]
        intents = []
        if source["status"] == "CONFIRMED" and isinstance(source["value"], list):
            for item in source["value"]:
                if isinstance(item, dict):
                    intents.append({"keyword": item.get("keyword"), "keyword_type": item.get("keyword_type"), "user_scenario": item.get("user_scenario"), "search_intent": item.get("search_intent"), "persona_unit": item.get("persona_unit"), "fact_ids": [source["fact_id"]]})
        self._store_validated("intent_intelligence", "intent_keyword_matrix", "schemas/intent-keyword-matrix-v4.schema.json", {"intents": intents, "fact_ids": [source["fact_id"]]}, ["fact_packet", "company_profile", "product_profile"])

    def _run_personas(self, facts):
        field_map = {
            "产品或服务描述": ("products", "main_businesses"), "产品或服务特点": ("core_capabilities", "competitive_advantages"),
            "品牌故事": ("company_name", "positioning", "brand_story", "development_history"), "用户痛点": ("user_pain_points", "use_cases"),
            "信任背书": ("evidence",), "客户案例": ("evidence",), "社会贡献": ("social_contributions", "environmental_contributions", "local_contributions", "public_welfare_actions"),
            "客户评价": ("evidence",), "创始人介绍": ("founder",),
        }
        units, all_ids = [], []
        for name in PERSONA_UNITS:
            confirmed, inferred, unknown, evidence_ids, missing = [], [], [], [], []
            for field in field_map[name]:
                fact = facts[field]
                if fact["status"] == "CONFIRMED":
                    confirmed.append(f"{field}：{_display(fact)}")
                    evidence_ids.append(fact["fact_id"])
                elif fact["status"] == "INFERRED":
                    inferred.append(f"{field}：{INFERRED}")
                    evidence_ids.append(fact["fact_id"])
                else:
                    unknown.append(CONFLICTED if fact["status"] == "CONFLICTED" else MISSING)
                    missing.append(field)
                    evidence_ids.append(fact["fact_id"])
            all_ids.extend(evidence_ids)
            units.append({"name": name, "confirmed_content": confirmed, "inferred_content": inferred, "unknown_content": unknown, "evidence_ids": evidence_ids, "missing_materials": missing, "forbidden_claims": []})
        self._store_validated("persona_intelligence", "nine_personas", "schemas/nine-personas-v4.schema.json", {"units": units, "fact_ids": all_ids}, ["fact_packet", "company_profile", "product_profile", "intent_keyword_matrix"])

    def _run_trust(self, facts):
        evidence = facts["evidence"]
        products = facts["products"]
        evidence_value = evidence["value"] if isinstance(evidence["value"], dict) else {}
        has_cases = isinstance(evidence_value.get("cases"), list) and bool(evidence_value["cases"])
        has_credentials = any(isinstance(evidence_value.get(key), list) and evidence_value[key] for key in ("qualifications", "certifications", "patents"))
        has_reviews = isinstance(evidence_value.get("reviews"), list) and bool(evidence_value["reviews"])
        dimensions = {
            "Expertise": 25 if facts["core_capabilities"]["status"] == "CONFIRMED" and products["status"] == "CONFIRMED" else 0,
            "Experience": 25 if has_cases else 0,
            "Authority": 25 if has_credentials else 0,
            "Trustworthiness": 25 if facts["official_website"]["status"] == "CONFIRMED" and facts["business_boundaries"]["status"] == "CONFIRMED" and has_reviews else 0,
        }
        gaps = [field for field in ("official_website", "core_capabilities", "products", "business_boundaries") if facts[field]["status"] != "CONFIRMED"]
        gaps.extend(label for label, present in (("evidence.cases", has_cases), ("evidence.qualifications", has_credentials), ("evidence.reviews", has_reviews)) if not present)
        self._store_validated("trust_intelligence", "trust_report", "schemas/trust-report-v4.schema.json", {"score": sum(dimensions.values()), "dimensions": dimensions, "gaps": gaps, "fact_ids": [facts[key]["fact_id"] for key in ("official_website", "core_capabilities", "products", "business_boundaries", "evidence")]}, ["fact_packet", "company_profile", "product_profile", "nine_personas"])

    def _run_keywords(self, facts):
        intent_artifact = self.store.get("intent_keyword_matrix")["payload"]
        company = facts["company_name"]
        keywords = [{"keyword": _display(company), "keyword_type": "品牌词", "product_or_service": _display(company), "user_scenario": "确认企业主体与官方资料", "search_intent": "品牌导航", "persona_unit": "品牌故事", "fact_ids": [company["fact_id"]], "evidence_status": company["status"], "risk_level": "低", "needs_confirmation": False}]
        for item in intent_artifact["intents"]:
            if not all(item.get(field) for field in ("keyword", "keyword_type", "user_scenario", "search_intent", "persona_unit")):
                raise PipelineBlocked("KEYWORD-005: user intent is incomplete; cannot generate a traceable keyword")
            if item["keyword_type"] not in KEYWORD_TYPES:
                raise PipelineBlocked("KEYWORD-006: user intent uses an unsupported keyword type")
            keywords.append({"keyword": item["keyword"], "keyword_type": item["keyword_type"], "product_or_service": "【由用户意图资料指定】", "user_scenario": item["user_scenario"], "search_intent": item["search_intent"], "persona_unit": item["persona_unit"], "fact_ids": item["fact_ids"], "evidence_status": "CONFIRMED", "risk_level": "中", "needs_confirmation": False})
        ids = [fact_id for item in keywords for fact_id in item["fact_ids"]]
        self._store_validated("keyword_intelligence", "keyword_matrix", "schemas/keyword-matrix-v4.schema.json", {"keywords": keywords, "fact_ids": ids}, ["fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report"])

    def _run_report(self, facts):
        company = self.store.get("company_profile")["payload"]
        trust = self.store.get("trust_report")["payload"]
        keywords = self.store.get("keyword_matrix")["payload"]
        fact_ids = sorted(set(company["fact_ids"] + trust["fact_ids"] + keywords["fact_ids"]))
        payload = {"current_state": [f"企业名称：{company['company_name']['display']}", f"企业定位：{company['positioning']['display']}", f"资料完整度：{trust['score']}/100（仅反映当前已提供资料）"], "gaps": [f"{field}：{MISSING}" for field in trust["gaps"]] or ["暂无已识别资料缺口"], "directions": ["先补齐 UNKNOWN 与 CONFLICTED 事实，再运行固定 Pipeline。", "仅使用绑定 fact_id 的关键词与画像开展 GEO 运营。"], "plan": [f"关键词：{item['keyword']}｜场景：{item['user_scenario']}" for item in keywords["keywords"]], "fact_ids": fact_ids}
        self._store_validated("geo_report", "geo_report", "schemas/final-report-v4.schema.json", payload, ["fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report", "keyword_matrix"])
        summary = {"company_name": company["company_name"]["display"], "pipeline_id": self.protocol.pipeline_id, "artifact_ids": [item["artifact_id"] for item in self.store.all()], "status": "VALIDATED"}
        contract = self.protocol.check_agent_permission("geo_report")
        self._fail(validate_agent_permissions(contract, "final_summary", summary) + validate_final_summary(summary))
        artifact = self.store.put("final_summary", "geo_report", "schemas/final-summary-v4.schema.json", summary, ["geo_report"], [])
        self.trace["stages"].append({"stage": "final_summary", "artifact_id": artifact["artifact_id"], "status": "VALIDATED"})

    def _store_validated(self, agent, artifact_type, schema, payload, inputs, validate=True):
        self.protocol.check_stage(agent, self.completed)
        contract = self.protocol.check_agent_permission(agent)
        issues = validate_agent_permissions(contract, artifact_type, payload)
        if validate:
            known_fact_ids = {fact["fact_id"] for fact in self.store.get("fact_packet")["payload"]["facts"]} if artifact_type != "fact_packet" else set()
            validators = {
                "fact_packet": lambda: validate_fact_packet(payload), "company_profile": lambda: validate_company_profile(payload, known_fact_ids),
                "product_profile": lambda: validate_product_profile(payload, known_fact_ids), "intent_keyword_matrix": lambda: validate_intent_matrix(payload, known_fact_ids),
                "nine_personas": lambda: validate_personas(payload, known_fact_ids), "trust_report": lambda: validate_trust_report(payload, known_fact_ids),
                "keyword_matrix": lambda: validate_keyword_matrix(payload, known_fact_ids), "geo_report": lambda: validate_final_report(payload, known_fact_ids),
            }
            issues.extend(validators[artifact_type]())
        self._fail(issues)
        artifact = self.store.put(artifact_type, agent, schema, payload, inputs, payload.get("fact_ids", []))
        self.completed.append(agent)
        self.trace["stages"].append({"stage": agent, "artifact_id": artifact["artifact_id"], "status": "VALIDATED"})

    def _fail(self, issues):
        self.trace["issues"].extend(item.as_dict() for item in issues)
        try:
            fail_closed(issues)
        except ValidationError as exc:
            raise PipelineBlocked(f"VALIDATION_BLOCKED: {exc}") from exc
