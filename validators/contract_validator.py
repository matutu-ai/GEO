"""Validation entry points for the versioned GEO/GEO-BD JSON contracts."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent


class ContractValidationError(ValueError):
    """Raised when a phase-0 collaboration contract is invalid."""


def _load_schema(name):
    path = ROOT / "schemas" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(instance, schema):
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ContractValidationError(details)


def _validate_unique_prescription_ids(payload):
    ids = [item["id"] for item in payload["prescriptions"]]
    if len(ids) != len(set(ids)):
        raise ContractValidationError("prescriptions.id: Prescription ID must be unique")


def _validate_unique_ids(items, field, label):
    ids = [item[field] for item in items]
    if len(ids) != len(set(ids)):
        raise ContractValidationError(f"{label}.{field}: IDs must be unique")


def _validate_identity(payload, upstream, label):
    for field in ("diagnostic_id", "company_id"):
        if payload.get(field) != upstream.get(field):
            raise ContractValidationError(f"{label}.{field}: must match upstream contract")


def _validate_references(items, field, available_ids, label):
    referenced = {value for item in items for value in item[field]}
    missing = sorted(referenced - set(available_ids))
    if missing:
        raise ContractValidationError(f"{label}.{field}: unknown IDs: {missing}")


def validate_geo_bd_handoff(payload):
    """Validate the standard GEO-BD -> GEO handoff and unique Prescription IDs."""
    schema = _load_schema("geo-bd-handoff-v1.schema.json")
    _validate(payload, schema)
    _validate_unique_prescription_ids(payload)


def validate_manual_prescription_input(payload):
    """Validate Manual Prescription with the exact shared Prescription object definition."""
    source = _load_schema("geo-bd-handoff-v1.schema.json")
    schema = {
        "$schema": source["$schema"],
        "$defs": source["$defs"],
        "$ref": "#/$defs/manualPrescriptionInput",
    }
    _validate(payload, schema)
    _validate_unique_prescription_ids(payload)


def validate_geo_strategy(payload, prescription_input):
    """Validate Strategy structure and resolve every reference against its input Prescription set."""
    _validate(payload, _load_schema("geo-strategy-v1.schema.json"))
    source_system = prescription_input.get("source_system")
    if source_system == "GEO-BD":
        validate_geo_bd_handoff(prescription_input)
    elif source_system == "MANUAL":
        validate_manual_prescription_input(prescription_input)
    else:
        raise ContractValidationError("source_system: must be GEO-BD or MANUAL")

    _validate_identity(payload, prescription_input, "strategy")
    _validate_unique_ids(payload["strategies"], "id", "strategies")

    available_ids = {item["id"] for item in prescription_input["prescriptions"]}
    _validate_references(payload["strategies"], "prescription_ids", available_ids, "strategies")


def validate_intent_strategy(payload, strategy_payload, prescription_input):
    """Validate Intent -> Strategy -> Prescription traceability."""
    _validate(payload, _load_schema("intent-strategy-v1.schema.json"))
    validate_geo_strategy(strategy_payload, prescription_input)
    _validate_identity(payload, strategy_payload, "intent")
    _validate_unique_ids(payload["intents"], "id", "intents")
    strategy_ids = {item["id"] for item in strategy_payload["strategies"]}
    prescription_ids = {item["id"] for item in prescription_input["prescriptions"]}
    _validate_references(payload["intents"], "strategy_ids", strategy_ids, "intents")
    _validate_references(payload["intents"], "prescription_ids", prescription_ids, "intents")


def validate_keyword_strategy(payload, strategy_payload, intent_payload, prescription_input):
    """Validate every Keyword reference to Intent, Strategy, Prescription and Fact IDs."""
    _validate(payload, _load_schema("keyword-strategy-v1.schema.json"))
    validate_intent_strategy(intent_payload, strategy_payload, prescription_input)
    _validate_identity(payload, strategy_payload, "keyword")
    _validate_unique_ids(payload["keywords"], "keyword_id", "keywords")
    strategy_ids = {item["id"] for item in strategy_payload["strategies"]}
    prescription_ids = {item["id"] for item in prescription_input["prescriptions"]}
    intent_ids = {item["id"] for item in intent_payload["intents"]}
    _validate_references(payload["keywords"], "strategy_ids", strategy_ids, "keywords")
    _validate_references(payload["keywords"], "prescription_ids", prescription_ids, "keywords")
    _validate_references(payload["keywords"], "intent_ids", intent_ids, "keywords")


def validate_persona_plan(payload, strategy_payload, prescription_input):
    """Validate fixed nine-persona plans and upstream references."""
    _validate(payload, _load_schema("persona-plan-v1.schema.json"))
    validate_geo_strategy(strategy_payload, prescription_input)
    _validate_identity(payload, strategy_payload, "persona")
    _validate_unique_ids(payload["personas"], "persona_id", "personas")
    strategy_ids = {item["id"] for item in strategy_payload["strategies"]}
    prescription_ids = {item["id"] for item in prescription_input["prescriptions"]}
    _validate_references(payload["personas"], "strategy_ids", strategy_ids, "personas")
    _validate_references(payload["personas"], "prescription_ids", prescription_ids, "personas")


def validate_user_persona_plan(payload, strategy_payload, prescription_input, keyword_payload):
    """Validate user decision personas and their traceability to keywords and upstream contracts."""
    _validate(payload, _load_schema("user-persona-plan-v1.schema.json"))
    validate_geo_strategy(strategy_payload, prescription_input)
    _validate_identity(payload, strategy_payload, "user_persona")
    _validate_unique_ids(payload["personas"], "user_persona_id", "user_personas")
    strategy_ids = {item["id"] for item in strategy_payload["strategies"]}
    prescription_ids = {item["id"] for item in prescription_input["prescriptions"]}
    keyword_ids = {item["keyword_id"] for item in keyword_payload["keywords"]}
    _validate_references(payload["personas"], "strategy_ids", strategy_ids, "user_personas")
    _validate_references(payload["personas"], "prescription_ids", prescription_ids, "user_personas")
    referenced_keywords = {keyword_id for item in payload["personas"] for keyword_id in item["keyword_ids"]}
    missing_keywords = sorted(referenced_keywords - keyword_ids)
    if missing_keywords:
        raise ContractValidationError(f"user_personas.keyword_ids: unknown IDs: {missing_keywords}")


def validate_guided_next_steps(payload, upstream):
    """Validate user-facing prompts and the recommended next decision."""
    _validate(payload, _load_schema("guided-next-steps-v1.schema.json"))
    _validate_identity(payload, upstream, "guided_next_steps")


def validate_retest_request(payload):
    """Validate a GEO -> GEO-BD request that asks for re-diagnosis without declaring results."""
    _validate(payload, _load_schema("geo-retest-request-v1.schema.json"))


def validate_execution_projection(
    payload, prescription_input, strategy_payload, intent_payload, keyword_payload, persona_payload,
    user_persona_payload, guidance_payload
):
    """Validate the closed standard projection without permitting parallel free-text objects."""
    _validate(payload, _load_schema("execution-v1.schema.json"))
    validate_keyword_strategy(keyword_payload, strategy_payload, intent_payload, prescription_input)
    validate_persona_plan(persona_payload, strategy_payload, prescription_input)
    validate_user_persona_plan(user_persona_payload, strategy_payload, prescription_input, keyword_payload)
    validate_guided_next_steps(guidance_payload, prescription_input)
    validate_retest_request(payload["retest_request"])
    _validate_identity(payload, prescription_input, "execution")

    expected = {
        "prescriptions": prescription_input["prescriptions"],
        "strategies": strategy_payload["strategies"],
        "intents": intent_payload["intents"],
        "keywords": keyword_payload["keywords"],
        "personas": persona_payload["personas"],
        "user_personas": user_persona_payload,
        "guided_next_steps": guidance_payload,
    }
    for field, value in expected.items():
        if payload[field] != value:
            raise ContractValidationError(f"execution.{field}: must embed the validated upstream artifact")

    prescription_ids = {item["id"] for item in prescription_input["prescriptions"]}
    strategy_ids = {item["id"] for item in strategy_payload["strategies"]}
    retest = payload["retest_request"]
    if set(retest["executed_prescription_ids"]) != prescription_ids:
        raise ContractValidationError("retest_request.executed_prescription_ids: must match execution")
    if set(retest["executed_strategy_ids"]) != strategy_ids:
        raise ContractValidationError("retest_request.executed_strategy_ids: must match execution")
