# SPDX-License-Identifier: Apache-2.0
"""Offline normalization of supplied execution results into auditable receipts."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .language import E7QError
from .temporal import temporal_evidence


def _digest(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def _load_json(path: str | Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        raise E7QError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise E7QError(f"{label} must be a JSON object")
    return value, raw


def load_execution_bundle(path: str | Path) -> tuple[dict[str, Any], bytes]:
    bundle, raw = _load_json(path, "execution bundle")
    if bundle.get("schema") != "e7q.execution-bundle/v1":
        raise E7QError("execution bundle must use e7q.execution-bundle/v1")
    if bundle.get("status") != "READY" or bundle.get("submitted") is not False:
        raise E7QError("execution bundle must be READY and not already submitted")
    return bundle, raw


def load_execution_result(path: str | Path) -> tuple[dict[str, Any], bytes]:
    result, raw = _load_json(path, "execution result")
    if result.get("schema") != "e7q.execution-result/v1":
        raise E7QError("execution result must use e7q.execution-result/v1")
    required = {"provider", "job_id", "target", "shots", "counts", "completed_at"}
    missing = required - result.keys()
    if missing:
        raise E7QError(f"execution result missing: {', '.join(sorted(missing))}")
    return result, raw


def build_execution_receipt(
    bundle: dict[str, Any],
    bundle_bytes: bytes,
    result: dict[str, Any],
    result_bytes: bytes,
) -> dict[str, object]:
    """Validate supplied evidence and build a deterministic offline receipt."""
    if result["target"] != bundle.get("target"):
        raise E7QError("execution result target does not match bundle")
    shots = result["shots"]
    if not isinstance(shots, int) or shots < 1 or shots != bundle.get("shots"):
        raise E7QError("execution result shots do not match bundle")
    counts = result["counts"]
    if not isinstance(counts, dict) or not counts:
        raise E7QError("execution result counts must be a non-empty object")
    width = None
    normalized: dict[str, int] = {}
    for outcome, count in counts.items():
        if not isinstance(outcome, str) or not outcome or set(outcome) - {"0", "1"}:
            raise E7QError("execution result outcomes must be binary strings")
        if width is None:
            width = len(outcome)
        if len(outcome) != width:
            raise E7QError("execution result outcomes must have equal width")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise E7QError("execution result counts must be non-negative integers")
        normalized[outcome] = count
    if sum(normalized.values()) != shots:
        raise E7QError("execution result counts must sum to shots")
    expected_bundle_digest = result.get("bundle_digest")
    actual_bundle_digest = _digest(bundle_bytes)
    if expected_bundle_digest is not None and expected_bundle_digest != actual_bundle_digest:
        raise E7QError("execution result bundle_digest does not match bundle")
    probabilities = {
        outcome: count / shots for outcome, count in sorted(normalized.items())
    }
    proof = [
        {
            "step": 0,
            "kind": "bundle-linkage",
            "bundle_digest": actual_bundle_digest,
            "source_digest": bundle.get("source_digest"),
            "openqasm_digest": bundle.get("openqasm_digest"),
        },
        {
            "step": 1,
            "kind": "supplied-result",
            "result_digest": _digest(result_bytes),
            "provider": result["provider"],
            "job_id": result["job_id"],
            "completed_at": result["completed_at"],
        },
        {
            "step": 2,
            "kind": "result-validation",
            "target": result["target"],
            "shots": shots,
            "count_total": sum(normalized.values()),
            "status": "PASS",
        },
        {
            "step": 3,
            "kind": "evidence-boundary",
            "boundary": (
                "Receipt validates internal consistency and bundle linkage of "
                "user-supplied data. E7Q did not authenticate the provider, submit "
                "or witness the job, or establish physical fidelity."
            ),
        },
    ]
    return {
        "schema": "e7q.execution-receipt/v1",
        "status": "PASS",
        "bundle_digest": actual_bundle_digest,
        "result_digest": _digest(result_bytes),
        "provider": result["provider"],
        "job_id": result["job_id"],
        "target": result["target"],
        "shots": shots,
        "completed_at": result["completed_at"],
        "temporal_evidence": temporal_evidence(
            carrier="TD0",
            carrier_description="one provider-reported execution-result event",
            order_relation="single reported completion point",
            chronology_status="provider-reported-not-authenticated",
            projection_from="user-supplied provider result",
            projection_to="normalized E7Q execution receipt",
            preserves=[
                "reported completion time",
                "bundle and result linkage",
                "counts and empirical probabilities",
            ],
            loses=[
                "shot-level ordering and timing",
                "intermediate quantum states",
                "provider-authenticated chronology",
            ],
            reconstruction_status="non-unique",
            reconstruction_limit=(
                "Multiple shot sequences and device histories can produce the "
                "same aggregate counts."
            ),
            clock={
                "field": "completed_at",
                "value": result["completed_at"],
                "status": "provider-reported-not-authenticated",
            },
            criterion="bundle linkage and count consistency",
            phase="PASS",
            boundary_crossing={"detected": False},
        ),
        "counts": dict(sorted(normalized.items())),
        "probabilities": probabilities,
        "proof": proof,
    }
