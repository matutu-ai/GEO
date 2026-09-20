"""Prescription-driven Standard Path kept separate from the legacy-compatible V4 pipeline."""

import json
from copy import deepcopy

from validators.contract_validator import (
    ContractValidationError,
    validate_execution_projection,
    validate_geo_bd_handoff,
    validate_geo_strategy,
    validate_intent_strategy,
    validate_keyword_strategy,
    validate_manual_prescription_input,
    validate_persona_plan,
    validate_retest_request,
)


STANDARD_STAGES = (
    "handoff_validation",
    "fact_normalization",
    "prescription_intake",
    "strategy_generation",
    "company_context",
    "product_context",
    "intent_strategy",
    "keyword_strategy",
    "persona_strategy",
    "execution_projection",
)
FACT_FIELDS = (
    "company_name", "official_website", "positioning", "main_businesses", "target_customers",
    "service_regions", "core_capabilities", "use_cases", "competitive_advantages",
    "business_boundaries", "products", "user_intents", "user_pain_points", "brand_story",
    "development_history", "evidence", "founder", "social_contributions",
    "environmental_contributions", "local_contributions", "public_welfare_actions",
)
STANDARD_REQUIRED_FACTS = (
    "company_name", "positioning", "main_businesses", "target_customers", "products",
)
KEYWORD_TYPES = ("品牌词", "搜索词", "问答词", "意图场景词")
KEYWORD_INTENTS = {
    "品牌词": ("品牌识别", "品牌故事"),
    "搜索词": ("业务检索", "产品或服务描述"),
    "问答词": ("问题解决", "用户痛点"),
    "意图场景词": ("场景决策", "产品或服务特点"),
}
PERSONA_UNITS = (
    "产品或服务描述", "产品或服务特点", "品牌故事", "用户痛点", "信任背书",
    "客户案例", "社会贡献", "客户评价", "创始人介绍",
)


class StandardPathBlocked(RuntimeError):
    """Fail-closed error for the Standard Path."""


def _present(value):
    return value is not None and value != "" and value != [] and value != {}


def _first_text(value):
    if isinstance(value, list):
        return _first_text(value[0]) if value else ""
    if isinstance(value, dict):
        for key in ("name", "title", "keyword"):
            if _present(value.get(key)):
                return str(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _summarize(value):
    if isinstance(value, list):
        return "；".join(_first_text(item) for item in value if _present(item))
    if isinstance(value, dict):
        return "；".join(f"{key}：{_summarize(item)}" for key, item in value.items() if _present(item))
    return str(value)


class StandardPathPipeline:
    """Minimal phase-1 runtime: Prescription -> Strategy -> projected execution."""

    def __init__(self):
        self.trace = {"pipeline_id": "geo-standard-path-v1", "stages": [], "status": "RUNNING"}
        self._handoff = None
        self._prescription_snapshot = None

    def run(self, handoff, company_data):
        try:
            validated_handoff = self._validate_handoff(handoff)
            fact_packet = self._normalize_facts(company_data)
            prescription_intake = self._intake_prescriptions(validated_handoff)
            strategy = self._generate_strategy(prescription_intake, fact_packet)
            company_context = self._company_context(fact_packet)
            product_context = self._product_context(fact_packet)
            intents = self._intent_strategy(prescription_intake, strategy, fact_packet)
            keywords = self._keyword_strategy(prescription_intake, strategy, intents, fact_packet)
            personas = self._persona_strategy(prescription_intake, strategy, fact_packet)
            execution, retest = self._execution_projection(
                prescription_intake, strategy, intents, keywords, personas, fact_packet
            )
        except ContractValidationError as exc:
            raise StandardPathBlocked(f"STANDARD_VALIDATION_BLOCKED: {exc}") from exc

        current_snapshot = json.dumps(
            prescription_intake["prescriptions"], ensure_ascii=False, sort_keys=True
        )
        if current_snapshot != self._prescription_snapshot:
            raise StandardPathBlocked("STANDARD-009: Prescription Intake is immutable")

        self.trace["status"] = "VALIDATED"
        return {
            "geo_strategy": strategy,
            "keyword_matrix": keywords,
            "persona_plan": personas,
            "execution": execution,
            "retest_request": retest,
            "company_context": company_context,
            "product_context": product_context,
            "intent_strategy": intents,
        }, deepcopy(self.trace)

    def _record(self, stage, artifact):
        expected = STANDARD_STAGES[len(self.trace["stages"])]
        if stage != expected:
            raise StandardPathBlocked(
                f"STANDARD-001: expected stage '{expected}', received '{stage}'"
            )
        self.trace["stages"].append({"stage": stage, "artifact": artifact, "status": "VALIDATED"})

    def _validate_handoff(self, handoff):
        if not isinstance(handoff, dict):
            raise StandardPathBlocked("STANDARD-002: handoff must be a JSON object")
        source_system = handoff.get("source_system")
        if source_system == "GEO-BD":
            validate_geo_bd_handoff(handoff)
        elif source_system == "MANUAL":
            validate_manual_prescription_input(handoff)
        else:
            raise StandardPathBlocked("STANDARD-003: source_system must be GEO-BD or MANUAL")
        validated = deepcopy(handoff)
        self._record("handoff_validation", "prescription_handoff")
        return validated

    def _normalize_facts(self, company_data):
        if not isinstance(company_data, dict):
            raise StandardPathBlocked("STANDARD-004: company input must be a JSON object")
        conflicts = company_data.get("conflicts", {})
        if not isinstance(conflicts, dict):
            raise StandardPathBlocked("STANDARD-005: conflicts must be an object")
        facts = []
        for index, field in enumerate(FACT_FIELDS, start=1):
            if field in conflicts:
                value, status = deepcopy(conflicts[field]), "CONFLICTED"
            elif _present(company_data.get(field)):
                value, status = deepcopy(company_data[field]), "CONFIRMED"
            else:
                value, status = None, "UNKNOWN"
            facts.append({
                "fact_id": f"fact-{index:03d}",
                "field": field,
                "value": value,
                "status": status,
                "source": f"input.{field}",
            })
        fact_map = {fact["field"]: fact for fact in facts}
        missing = [field for field in STANDARD_REQUIRED_FACTS if fact_map[field]["status"] != "CONFIRMED"]
        if missing:
            raise StandardPathBlocked(
                f"STANDARD-006: Standard Path requires confirmed company facts: {missing}"
            )
        packet = {"facts": facts, "fact_map": fact_map}
        self._record("fact_normalization", "confirmed_fact_packet")
        return packet

    def _intake_prescriptions(self, handoff):
        intake = {
            "diagnostic_id": handoff["diagnostic_id"],
            "company_id": handoff["company_id"],
            "source_system": handoff["source_system"],
            "prescriptions": deepcopy(handoff["prescriptions"]),
        }
        self._handoff = deepcopy(handoff)
        self._prescription_snapshot = json.dumps(
            intake["prescriptions"], ensure_ascii=False, sort_keys=True
        )
        self._record("prescription_intake", "readonly_prescription_intake")
        return intake

    def _confirmed_fact_ids(self, fact_packet):
        return [
            fact["fact_id"] for fact in fact_packet["facts"] if fact["status"] == "CONFIRMED"
        ]

    def _generate_strategy(self, intake, fact_packet):
        fact_ids = self._confirmed_fact_ids(fact_packet)
        strategies = []
        for index, prescription in enumerate(intake["prescriptions"], start=1):
            strategies.append({
                "id": f"STRATEGY-{index:03d}",
                "prescription_ids": [prescription["id"]],
                "objective": (
                    f"执行处方“{prescription['statement']}”：围绕已确认企业事实建立 GEO 关键词、"
                    "画像与后续执行覆盖"
                ),
                "priority": prescription["priority"],
                "execution_scope": ["keyword", "persona", "content", "source", "publishing", "retest"],
                "fact_ids": fact_ids,
            })
        payload = {
            "strategy_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "strategies": strategies,
        }
        validate_geo_strategy(payload, self._handoff)
        self._record("strategy_generation", "geo_strategy")
        return payload

    def _company_context(self, fact_packet):
        facts = fact_packet["fact_map"]
        fields = ("company_name", "positioning", "main_businesses", "target_customers", "service_regions")
        context = {
            "values": {field: deepcopy(facts[field]["value"]) for field in fields if facts[field]["status"] == "CONFIRMED"},
            "fact_ids": [facts[field]["fact_id"] for field in fields if facts[field]["status"] == "CONFIRMED"],
            "role": "EXECUTION_CONTEXT_ONLY",
        }
        self._record("company_context", "company_execution_context")
        return context

    def _product_context(self, fact_packet):
        fact = fact_packet["fact_map"]["products"]
        context = {
            "products": deepcopy(fact["value"]),
            "fact_ids": [fact["fact_id"]],
            "role": "EXECUTION_CONTEXT_ONLY",
        }
        self._record("product_context", "product_execution_context")
        return context

    def _intent_strategy(self, intake, strategy_payload, fact_packet):
        facts = fact_packet["fact_map"]
        scenario_fact = facts["use_cases"] if facts["use_cases"]["status"] == "CONFIRMED" else facts["main_businesses"]
        target_fact = facts["target_customers"]
        prescription_map = {item["id"]: item for item in intake["prescriptions"]}
        intents = []
        for index, strategy in enumerate(strategy_payload["strategies"], start=1):
            prescription = prescription_map[strategy["prescription_ids"][0]]
            intents.append({
                "id": f"INTENT-{index:03d}",
                "strategy_ids": [strategy["id"]],
                "prescription_ids": list(strategy["prescription_ids"]),
                "intent": f"落实处方：{prescription['statement']}",
                "scenario": _first_text(scenario_fact["value"]),
                "target_user": _first_text(target_fact["value"]),
                "fact_ids": sorted({scenario_fact["fact_id"], target_fact["fact_id"]}),
            })
        payload = {
            "intent_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "intents": intents,
        }
        validate_intent_strategy(payload, strategy_payload, self._handoff)
        self._record("intent_strategy", "intent_strategy")
        return payload

    def _keyword_strategy(self, intake, strategy_payload, intent_payload, fact_packet):
        facts = fact_packet["fact_map"]
        company = _first_text(facts["company_name"]["value"])
        business = _first_text(facts["main_businesses"]["value"])
        product = _first_text(facts["products"]["value"])
        supplied_intents = facts["user_intents"]["value"] if facts["user_intents"]["status"] == "CONFIRMED" else []
        keywords = []
        keyword_map = {}
        for intent in intent_payload["intents"]:
            candidates = [
                {"keyword": company, "keyword_type": "品牌词"},
                {"keyword": f"{company} {business}", "keyword_type": "搜索词"},
                {"keyword": f"{business}如何选择", "keyword_type": "问答词"},
                {"keyword": f"{intent['scenario']} {business}", "keyword_type": "意图场景词"},
            ]
            if isinstance(supplied_intents, list):
                candidates.extend(
                    {
                        "keyword": item.get("keyword"),
                        "keyword_type": item.get("keyword_type"),
                        "user_scenario": item.get("user_scenario"),
                        "search_intent": item.get("search_intent"),
                        "persona_unit": item.get("persona_unit"),
                    }
                    for item in supplied_intents
                    if isinstance(item, dict)
                    and _present(item.get("keyword"))
                    and item.get("keyword_type") in KEYWORD_TYPES
                )
            fact_ids = sorted(set(intent["fact_ids"] + [facts["company_name"]["fact_id"], facts["main_businesses"]["fact_id"]]))
            for candidate in candidates:
                keyword = candidate["keyword"]
                keyword_type = candidate["keyword_type"]
                intent_label, persona_unit = KEYWORD_INTENTS[keyword_type]
                key = (keyword, keyword_type)
                if key not in keyword_map:
                    keyword_map[key] = {
                        "keyword_id": f"KEYWORD-{len(keyword_map) + 1:03d}",
                        "keyword": keyword,
                        "keyword_type": keyword_type,
                        "product_or_service": product,
                        "user_scenario": candidate.get("user_scenario") or intent["scenario"],
                        "search_intent": candidate.get("search_intent") or intent_label,
                        "persona_unit": candidate.get("persona_unit") if candidate.get("persona_unit") in PERSONA_UNITS else persona_unit,
                        "fact_ids": sorted(set(fact_ids + ([facts["user_intents"]["fact_id"]] if candidate.get("user_scenario") else []))),
                        "prescription_ids": list(intent["prescription_ids"]),
                        "strategy_ids": list(intent["strategy_ids"]),
                        "intent_ids": [intent["id"]],
                        "evidence_status": "CONFIRMED",
                        "risk_level": "低",
                        "needs_confirmation": True,
                    }
                else:
                    current = keyword_map[key]
                    current["fact_ids"] = sorted(set(current["fact_ids"] + fact_ids))
                    current["prescription_ids"] = sorted(set(current["prescription_ids"] + intent["prescription_ids"]))
                    current["strategy_ids"] = sorted(set(current["strategy_ids"] + intent["strategy_ids"]))
                    current["intent_ids"] = sorted(set(current["intent_ids"] + [intent["id"]]))
        keywords = list(keyword_map.values())
        payload = {
            "keyword_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "keywords": keywords,
        }
        validate_keyword_strategy(payload, strategy_payload, intent_payload, self._handoff)
        self._record("keyword_strategy", "keyword_matrix")
        return payload

    def _persona_strategy(self, intake, strategy_payload, fact_packet):
        facts = fact_packet["fact_map"]
        mappings = {
            "产品或服务描述": ("products", "main_businesses"),
            "产品或服务特点": ("core_capabilities", "competitive_advantages"),
            "品牌故事": ("brand_story", "development_history", "positioning"),
            "用户痛点": ("user_pain_points", "use_cases"),
            "信任背书": ("evidence",),
            "客户案例": ("evidence",),
            "社会贡献": ("social_contributions", "environmental_contributions", "local_contributions", "public_welfare_actions"),
            "客户评价": ("evidence",),
            "创始人介绍": ("founder",),
        }
        evidence_keys = {"信任背书": ("qualifications", "certifications", "patents"), "客户案例": ("cases",), "客户评价": ("reviews",)}
        strategy_ids = [item["id"] for item in strategy_payload["strategies"]]
        prescription_ids = [item["id"] for item in intake["prescriptions"]]
        personas = []
        for index, name in enumerate(PERSONA_UNITS, start=1):
            values, fact_ids = [], []
            missing_materials = []
            for field in mappings[name]:
                fact = facts[field]
                if fact["status"] != "CONFIRMED":
                    missing_materials.append(field)
                    continue
                value = fact["value"]
                if field == "evidence" and name in evidence_keys and isinstance(value, dict):
                    value = {key: value[key] for key in evidence_keys[name] if _present(value.get(key))}
                    if not value:
                        missing_materials.extend(f"evidence.{key}" for key in evidence_keys[name])
                if _present(value):
                    values.append(_summarize(value))
                    fact_ids.append(fact["fact_id"])
            ready = bool(values)
            missing_materials.extend(
                field for field in mappings[name]
                if facts[field]["status"] == "CONFIRMED" and not _present(facts[field]["value"])
                and field not in missing_materials
            )
            personas.append({
                "persona_id": f"PERSONA-{index:03d}",
                "name": name,
                "focus": "；".join(values) if ready else "NOT_IMPLEMENTED：缺少已确认资料，不生成未经确认内容",
                "status": "READY" if ready else "NOT_IMPLEMENTED",
                "confirmed_content": values,
                "unknown_content": [] if ready else ["【需企业提供真实佐证】"],
                "missing_materials": missing_materials,
                "forbidden_claims": ["未绑定事实来源的案例、评价、资质和数据不得对外发布"],
                "fact_ids": sorted(set(fact_ids)) or [facts["company_name"]["fact_id"]],
                "prescription_ids": prescription_ids,
                "strategy_ids": strategy_ids,
            })
        payload = {
            "persona_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "personas": personas,
        }
        validate_persona_plan(payload, strategy_payload, self._handoff)
        self._record("persona_strategy", "persona_plan")
        return payload

    def _execution_projection(self, intake, strategy, intents, keywords, personas, fact_packet):
        confirmed = [fact for fact in fact_packet["facts"] if fact["status"] == "CONFIRMED"]
        missing = [fact["field"] for fact in fact_packet["facts"] if fact["status"] != "CONFIRMED"]
        retest = {
            "retest_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "source_system": "GEO",
            "target_system": "GEO-BD",
            "executed_prescription_ids": [item["id"] for item in intake["prescriptions"]],
            "executed_strategy_ids": [item["id"] for item in strategy["strategies"]],
            "retest_targets": ["AI_VISIBILITY", "QUERY_COVERAGE", "CITATION_COVERAGE"],
        }
        validate_retest_request(retest)
        execution = {
            "execution_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "source_system": intake["source_system"],
            "prescriptions": deepcopy(intake["prescriptions"]),
            "strategies": deepcopy(strategy["strategies"]),
            "intents": deepcopy(intents["intents"]),
            "keywords": deepcopy(keywords["keywords"]),
            "personas": deepcopy(personas["personas"]),
            "evidence_readiness": {
                "status": "REFERENCE_ONLY",
                "confirmed_fact_count": len(confirmed),
                "total_fact_count": len(fact_packet["facts"]),
                "missing_fact_fields": missing,
                "fact_ids": [fact["fact_id"] for fact in confirmed],
            },
            "content_projection": {"status": "NOT_IMPLEMENTED"},
            "source_projection": {"status": "NOT_IMPLEMENTED"},
            "publishing_projection": {"status": "NOT_IMPLEMENTED"},
            "retest_request": deepcopy(retest),
        }
        validate_execution_projection(
            execution, self._handoff, strategy, intents, keywords, personas
        )
        self._record("execution_projection", "execution")
        return execution, retest
