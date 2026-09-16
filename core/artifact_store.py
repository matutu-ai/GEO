"""Validated immutable artifacts shared by fixed pipeline stages."""

from copy import deepcopy
from datetime import datetime, timezone

from core.execution_protocol import ProtocolViolation


class ArtifactStore:
    def __init__(self):
        self._artifacts = {}

    def put(self, artifact_type, producer, schema, payload, input_artifacts, fact_ids):
        if artifact_type in self._artifacts:
            raise ProtocolViolation(f"ARTIFACT-001: immutable artifact already exists: {artifact_type}")
        artifact = {
            "artifact_id": f"artifact-{len(self._artifacts) + 1:03d}",
            "artifact_type": artifact_type, "producer": producer, "version": "4.0.0",
            "schema": schema, "input_artifacts": list(input_artifacts),
            "fact_ids": sorted(set(fact_ids)), "status": "VALIDATED",
            "created_at": datetime.now(timezone.utc).isoformat(), "payload": deepcopy(payload),
        }
        self._artifacts[artifact_type] = artifact
        return deepcopy(artifact)

    def get(self, artifact_type):
        if artifact_type not in self._artifacts:
            raise ProtocolViolation(f"ARTIFACT-002: required artifact not available: {artifact_type}")
        artifact = self._artifacts[artifact_type]
        if artifact["status"] != "VALIDATED":
            raise ProtocolViolation(f"ARTIFACT-003: artifact is not validated: {artifact_type}")
        return deepcopy(artifact)

    def all(self):
        return [deepcopy(item) for item in self._artifacts.values()]
