"""Prescription-driven Standard Path kept separate from the legacy-compatible V4 pipeline."""

import json
from copy import deepcopy

from validators.contract_validator import (
    ContractValidationError,
    validate_execution_projection,
    validate_geo_bd_handoff,
    validate_geo_strategy,
    validate_guided_next_steps,
    validate_intent_strategy,
    validate_keyword_strategy,
    validate_manual_prescription_input,
    validate_persona_plan,
    validate_retest_request,
    validate_user_persona_plan,
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
    "user_persona_strategy",
    "guidance_projection",
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
        self._preferences = {}

    def run(self, handoff, company_data):
        try:
            self._preferences = self._read_preferences(company_data)
            validated_handoff = self._validate_handoff(handoff)
            fact_packet = self._normalize_facts(company_data)
            prescription_intake = self._intake_prescriptions(validated_handoff)
            strategy = self._generate_strategy(prescription_intake, fact_packet)
            company_context = self._company_context(fact_packet)
            product_context = self._product_context(fact_packet)
            intents = self._intent_strategy(prescription_intake, strategy, fact_packet)
            keywords = self._keyword_strategy(prescription_intake, strategy, intents, fact_packet)
            personas = self._persona_strategy(prescription_intake, strategy, fact_packet)
            user_personas = self._user_persona_strategy(
                prescription_intake, strategy, keywords, fact_packet
            )
            guidance = self._guidance_projection(
                prescription_intake, strategy, fact_packet, keywords, personas, user_personas
            )
            execution, retest = self._execution_projection(
                prescription_intake, strategy, intents, keywords, personas, user_personas,
                guidance, fact_packet
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
            "user_persona_plan": user_personas,
            "guided_next_steps": guidance,
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

    def _read_preferences(self, company_data):
        raw = company_data.get("geo_preferences", {}) if isinstance(company_data, dict) else {}
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise StandardPathBlocked("STANDARD-010: geo_preferences must be an object")
        delivery_mode = raw.get("delivery_mode", "完整版")
        if delivery_mode not in ("简约版", "完整版"):
            raise StandardPathBlocked("STANDARD-011: delivery_mode must be 简约版 or 完整版")
        list_fields = ("requested_keywords", "excluded_keywords", "approved_keywords", "user_personas")
        for field in list_fields:
            if field in raw and not isinstance(raw[field], list):
                raise StandardPathBlocked(f"STANDARD-012: geo_preferences.{field} must be an array")
        return {
            "provided": "geo_preferences" in company_data,
            "delivery_mode": delivery_mode,
            "primary_objective": str(raw.get("primary_objective", "关键词与画像整理")),
            "vertical_business": str(raw.get("vertical_business", "")),
            "requested_keywords": deepcopy(raw.get("requested_keywords", [])),
            "excluded_keywords": deepcopy(raw.get("excluded_keywords", [])),
            "approved_keywords": deepcopy(raw.get("approved_keywords", [])),
            "user_personas": deepcopy(raw.get("user_personas", [])),
        }

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
        supplied_candidates = []
        if isinstance(supplied_intents, list):
            supplied_candidates.extend(
                {
                    "keyword": item.get("keyword"),
                    "keyword_type": item.get("keyword_type"),
                    "user_scenario": item.get("user_scenario"),
                    "search_intent": item.get("search_intent"),
                    "persona_unit": item.get("persona_unit"),
                    "_origin": "CLIENT_REQUESTED",
                    "_from_user_intents": True,
                }
                for item in supplied_intents
                if isinstance(item, dict)
                and _present(item.get("keyword"))
                and item.get("keyword_type") in KEYWORD_TYPES
            )
        for item in self._preferences["requested_keywords"]:
            if isinstance(item, str) and _present(item):
                supplied_candidates.append({
                    "keyword": item,
                    "keyword_type": "搜索词",
                    "_origin": "CLIENT_REQUESTED",
                })
            elif isinstance(item, dict) and _present(item.get("keyword")):
                supplied_candidates.append({
                    "keyword": item["keyword"],
                    "keyword_type": item.get("keyword_type", "搜索词"),
                    "user_scenario": item.get("user_scenario"),
                    "search_intent": item.get("search_intent"),
                    "persona_unit": item.get("persona_unit"),
                    "_origin": "CLIENT_REQUESTED",
                })
        keywords = []
        keyword_map = {}
        for intent in intent_payload["intents"]:
            candidates = [
                {"keyword": company, "keyword_type": "品牌词", "_origin": "SYSTEM_RECOMMENDED"},
                {"keyword": f"{company} {business}", "keyword_type": "搜索词", "_origin": "SYSTEM_RECOMMENDED"},
                {"keyword": f"{business}如何选择", "keyword_type": "问答词", "_origin": "SYSTEM_RECOMMENDED"},
                {"keyword": f"{intent['scenario']} {business}", "keyword_type": "意图场景词", "_origin": "SYSTEM_RECOMMENDED"},
            ]
            candidates.extend(supplied_candidates)
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
                        "keyword_origin": candidate.get("_origin", "SYSTEM_RECOMMENDED"),
                        "decision_status": (
                            "CONFIRMED" if keyword in self._preferences["approved_keywords"]
                            else "PENDING_CONFIRMATION" if candidate.get("_origin") == "CLIENT_REQUESTED"
                            else "RECOMMENDED"
                        ),
                    }
                else:
                    current = keyword_map[key]
                    current["fact_ids"] = sorted(set(current["fact_ids"] + fact_ids))
                    current["prescription_ids"] = sorted(set(current["prescription_ids"] + intent["prescription_ids"]))
                    current["strategy_ids"] = sorted(set(current["strategy_ids"] + intent["strategy_ids"]))
                    current["intent_ids"] = sorted(set(current["intent_ids"] + [intent["id"]]))
                    if candidate.get("_origin") == "CLIENT_REQUESTED":
                        current["keyword_origin"] = "CLIENT_REQUESTED"
                        current["decision_status"] = (
                            "CONFIRMED" if keyword in self._preferences["approved_keywords"]
                            else "PENDING_CONFIRMATION"
                        )
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

    def _user_persona_strategy(self, intake, strategy_payload, keyword_payload, fact_packet):
        facts = fact_packet["fact_map"]
        target_value = facts["target_customers"]["value"]
        raw_personas = self._preferences["user_personas"]
        if raw_personas:
            source_items = raw_personas[:5]
            status = "CONFIRMED"
        elif isinstance(target_value, list):
            source_items = target_value[:5]
            status = "NEEDS_CONFIRMATION"
        else:
            source_items = [target_value]
            status = "NEEDS_CONFIRMATION"
        scenario_value = facts["use_cases"]["value"] if facts["use_cases"]["status"] == "CONFIRMED" else facts["main_businesses"]["value"]
        scenario = _first_text(scenario_value)
        business = _first_text(facts["main_businesses"]["value"])
        pain_value = facts["user_pain_points"]["value"] if facts["user_pain_points"]["status"] == "CONFIRMED" else []
        criteria_value = facts["competitive_advantages"]["value"] if facts["competitive_advantages"]["status"] == "CONFIRMED" else []
        supplied_queries = [
            item for item in (facts["user_intents"]["value"] if facts["user_intents"]["status"] == "CONFIRMED" else [])
            if isinstance(item, dict) and _present(item.get("keyword"))
        ]
        strategy_ids = [item["id"] for item in strategy_payload["strategies"]]
        prescription_ids = [item["id"] for item in intake["prescriptions"]]
        base_fact_ids = [facts["target_customers"]["fact_id"], facts["main_businesses"]["fact_id"]]
        if facts["use_cases"]["status"] == "CONFIRMED":
            base_fact_ids.append(facts["use_cases"]["fact_id"])
        for field in ("user_pain_points", "competitive_advantages", "user_intents"):
            if facts[field]["status"] == "CONFIRMED":
                base_fact_ids.append(facts[field]["fact_id"])
        personas = []
        for index, item in enumerate(source_items, start=1):
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("role") or item.get("title") or f"用户画像 {index}")
                audience = str(item.get("audience") or item.get("description") or name)
                item_scenario = str(item.get("scenario") or scenario)
                decision_stage = str(item.get("decision_stage") or "认知期→考虑期→决策期")
                pain_points = self._string_list(item.get("pain_points")) or self._string_list(pain_value)
                criteria = self._string_list(item.get("decision_criteria")) or self._string_list(criteria_value)
                queries = self._string_list(item.get("query_patterns"))
                query_status = "CLIENT_REQUESTED" if queries else "SYSTEM_RECOMMENDED"
            else:
                name = _first_text(item) or f"用户画像 {index}"
                audience = name
                item_scenario = scenario
                decision_stage = "认知期→考虑期→决策期"
                pain_points = self._string_list(pain_value)
                criteria = self._string_list(criteria_value)
                queries = []
                query_status = "SYSTEM_RECOMMENDED"
            if not queries:
                queries = [f"{business}是什么", f"{business}怎么选", f"{item_scenario}{business}怎么做"]
            related_keyword_ids = [
                keyword["keyword_id"] for keyword in keyword_payload["keywords"]
                if keyword["user_scenario"] == item_scenario
            ]
            personas.append({
                "user_persona_id": f"USER-PERSONA-{index:03d}",
                "name": name,
                "audience": audience,
                "scenario": item_scenario,
                "decision_stage": decision_stage,
                "pain_points": pain_points,
                "decision_criteria": criteria,
                "query_patterns": queries,
                "query_pattern_status": query_status,
                "status": status,
                "keyword_ids": sorted(set(related_keyword_ids)),
                "fact_ids": sorted(set(base_fact_ids)),
                "prescription_ids": prescription_ids,
                "strategy_ids": strategy_ids,
            })
        payload = {
            "user_persona_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "personas": personas,
        }
        validate_user_persona_plan(payload, strategy_payload, self._handoff, keyword_payload)
        self._record("user_persona_strategy", "user_persona_plan")
        return payload

    @staticmethod
    def _string_list(value):
        if isinstance(value, list):
            return [str(item) for item in value if _present(item)]
        if _present(value):
            return [str(value)]
        return []

    def _guidance_projection(self, intake, strategy_payload, fact_packet, keyword_payload, persona_payload, user_persona_payload):
        preferences = self._preferences
        custom_personas = bool(preferences["user_personas"])
        keyword_review_complete = bool(preferences["approved_keywords"])
        stages = [
            {
                "stage_id": "delivery_selection",
                "name": "选择交付版本与业务目标",
                "status": "COMPLETE" if preferences["provided"] else "READY_FOR_REVIEW",
                "prompt": "请选择简约版或完整版，并说明本次优先目标：品牌识别、业务获客、招商代理、用户教育或转化。",
                "recommendation": "没有明确目标时，先使用完整版，但暂停正式导出，等待客户确认主业务线。",
                "requires_user_confirmation": not preferences["provided"],
            },
            {
                "stage_id": "evidence_confirmation",
                "name": "确认资料与证据边界",
                "status": "READY_FOR_REVIEW",
                "prompt": "请确认企业主体、品牌名称、产品/服务、目标客户、业务边界，以及哪些资料可以公开引用。",
                "recommendation": "主体关系、费用、案例、评价、资质和效果数字没有证据时保持待确认。",
                "requires_user_confirmation": True,
            },
            {
                "stage_id": "user_persona_confirmation",
                "name": "确认用户决策画像",
                "status": "COMPLETE" if custom_personas else "NEEDS_CONFIRMATION",
                "prompt": "请确认 3—5 类重点用户：身份、场景、痛点、决策标准、阶段和典型问题。",
                "recommendation": "如果用户画像尚未确认，下一步优先完成用户画像，不建议先扩写企业九大画像。",
                "requires_user_confirmation": not custom_personas,
            },
            {
                "stage_id": "keyword_review",
                "name": "确认关键词分层",
                "status": "COMPLETE" if keyword_review_complete else "READY_FOR_REVIEW",
                "prompt": "请按品牌词、搜索词、问答词、意图场景词分别标记保留、修改、删除或待确认，并决定系统推荐词是否加入正式词库。",
                "recommendation": "先完成四类关键词确认；系统推荐词仅作参考，不自动视为已批准。",
                "requires_user_confirmation": not keyword_review_complete,
            },
            {
                "stage_id": "enterprise_persona_review",
                "name": "确认企业九大画像",
                "status": "READY_FOR_REVIEW",
                "prompt": "请逐项确认九大画像中哪些可以对外表达，哪些需要补资料，哪些本次不做。",
                "recommendation": "用户决策画像确认后，再补企业九大画像；客户案例、评价、社会贡献和创始人介绍不得凭空补齐。",
                "requires_user_confirmation": True,
            },
            {
                "stage_id": "next_skill_decision",
                "name": "选择后续技能",
                "status": "COMPLETE",
                "prompt": "关键词和画像确认后，是否继续生成 AI 推广总结，或暂时只保留当前词与画像交付？",
                "recommendation": "先确认词和画像，再考虑 AI 推广总结；不要跳过证据确认直接进入内容发布或平台验证。",
                "requires_user_confirmation": True,
            },
        ]
        if not custom_personas:
            next_stage = "user_persona_confirmation"
            next_prompt = stages[2]["prompt"]
        elif not keyword_review_complete:
            next_stage = "keyword_review"
            next_prompt = stages[3]["prompt"]
        else:
            next_stage = "enterprise_persona_review"
            next_prompt = stages[4]["prompt"]
        payload = {
            "guidance_version": "1.0.0",
            "diagnostic_id": intake["diagnostic_id"],
            "company_id": intake["company_id"],
            "delivery_mode": preferences["delivery_mode"],
            "vertical_business": preferences["vertical_business"] or _first_text(fact_packet["fact_map"]["main_businesses"]["value"]),
            "current_stage": "standard_export_review",
            "recommended_next_stage": next_stage,
            "next_prompt": next_prompt,
            "decision_required": True,
            "keyword_review": {
                "client_requested": [
                    item if isinstance(item, str) else item.get("keyword", "")
                    for item in preferences["requested_keywords"]
                    if (isinstance(item, str) and _present(item)) or (isinstance(item, dict) and _present(item.get("keyword")))
                ],
                "approved": [str(item) for item in preferences["approved_keywords"] if _present(item)],
                "excluded": [
                    item if isinstance(item, str) else item.get("keyword", "")
                    for item in preferences["excluded_keywords"]
                    if (isinstance(item, str) and _present(item)) or (isinstance(item, dict) and _present(item.get("keyword")))
                ],
            },
            "stages": stages,
            "optimization_directions": [
                {
                    "priority": "P0",
                    "title": "确认用户决策画像与关键词分层",
                    "reason": "画像决定关键词面向谁，关键词分层决定哪些词可以进入正式交付。",
                    "next_action": "先确认四类关键词的保留、修改、删除和待确认状态，再进入用户画像与企业九大画像确认。",
                    "status": "NEEDS_CONFIRMATION" if not custom_personas or not keyword_review_complete else "READY",
                },
                {
                    "priority": "P1",
                    "title": "补齐企业九大画像证据",
                    "reason": "品牌故事、信任背书、案例、评价和创始人介绍需要可核验资料。",
                    "next_action": "只补客户允许公开且有来源的材料，缺失部分保持待补。",
                    "status": "NEEDS_CONFIRMATION",
                },
                {
                    "priority": "P2",
                    "title": "内容、信源、发布与复测",
                    "reason": "这些属于后续执行阶段，不应在词和画像尚未确认时提前展开。",
                    "next_action": "词和画像确认后，再由用户单独授权进入后续阶段。",
                    "status": "NOT_IN_SCOPE",
                },
            ],
            "skill_recommendations": [
                {
                    "skill": "geo-keyword-persona",
                    "when": "用户决策画像或关键词仍需确认时",
                    "reason": "继续细化画像、认知/考虑/决策阶段和自然语言问题词。",
                    "next_decision": "确认哪些画像与词进入正式交付。",
                },
                {
                    "skill": "ai-promotion-summary",
                    "when": "关键词和画像已确认，准备形成品牌词、业务词和推广方向时",
                    "reason": "把已确认的词和画像转成 AI 推广总结与可执行建议。",
                    "next_decision": "决定先做推广总结，还是进入内容/信源阶段。",
                },
            ],
        }
        validate_guided_next_steps(payload, {"diagnostic_id": intake["diagnostic_id"], "company_id": intake["company_id"]})
        self._record("guidance_projection", "guided_next_steps")
        return payload

    def _execution_projection(self, intake, strategy, intents, keywords, personas, user_personas, guidance, fact_packet):
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
            "user_personas": deepcopy(user_personas),
            "guided_next_steps": deepcopy(guidance),
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
            execution, self._handoff, strategy, intents, keywords, personas, user_personas, guidance
        )
        self._record("execution_projection", "execution")
        return execution, retest
