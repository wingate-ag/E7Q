# SPDX-License-Identifier: Apache-2.0
"""Machine-readable conformance checks for E7Q offline artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .language import E7QError
from .observations import conformance_checks as observation_conformance_checks
from .temporal import conformance_checks as temporal_conformance_checks


_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "e7q.calibration/v1": ("captured_at", "targets"),
    "e7q.execution-bundle/v1": ("status", "target", "shots", "proof"),
    "e7q.execution-result/v1": ("target", "shots", "counts"),
    "e7q.execution-receipt/v1": ("target", "shots", "counts", "proof"),
    "e7q.execution-assessment/v1": ("status", "proof"),
    "e7q.replication-report/v1": ("status", "target", "total_shots", "pooled_counts", "proof"),
    "e7q.drift-report/v1": ("status", "target", "proof"),
    "e7q.trend-report/v1": ("status", "target", "campaigns", "series", "proof"),
}


def load_artifact(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise E7QError(f"invalid artifact JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise E7QError("artifact must be a JSON object")
    return value


def validate_artifact(value: dict[str, Any]) -> dict[str, object]:
    """Validate the stable identity and required top-level evidence of an artifact."""
    schema = value.get("schema")
    checks: list[dict[str, object]] = []
    known = isinstance(schema, str) and schema in _REQUIREMENTS
    checks.append({"name": "known-schema", "passed": known, "value": schema})
    required = _REQUIREMENTS.get(str(schema), ())
    for field in required:
        checks.append({
            "name": f"required-field:{field}",
            "passed": field in value and value[field] is not None,
        })
    if "proof" in required and "proof" in value:
        proof = value["proof"]
        checks.append({
            "name": "proof-sequence",
            "passed": isinstance(proof, list) and bool(proof),
        })
    if "temporal_evidence" in value:
        checks.extend(temporal_conformance_checks(value["temporal_evidence"]))
    if "observational_claim_pilot" in value:
        checks.extend(
            observation_conformance_checks(value["observational_claim_pilot"])
        )
    passed = all(bool(check["passed"]) for check in checks)
    status = "PASS" if passed else "FAIL"
    conformance = "STRUCTURALLY_CONFORMANT" if passed else "NONCONFORMANT"
    return {
        "schema": "e7q.conformance-report/v1",
        "status": status,
        "conformance": conformance,
        "validation_scope": "structure-only",
        "artifact_schema": schema,
        "checks": checks,
        "proof": [
            {
                "step": 0,
                "kind": "artifact-conformance",
                "artifact_schema": schema,
                "registered_schema": known,
            },
            {
                "step": 1,
                "kind": "conformance-decision",
                "status": status,
                "conformance": conformance,
            },
            {
                "step": 2,
                "kind": "evidence-boundary",
                "boundary": (
                    "Structural offline validation only; not semantic recomputation, "
                    "provider authentication, hardware execution, or physical-fidelity evidence."
                ),
            },
        ],
    }
