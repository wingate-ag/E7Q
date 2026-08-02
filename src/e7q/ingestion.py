# SPDX-License-Identifier: Apache-2.0
"""Offline vendor-export normalization for E7Q calibration snapshots."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .language import E7QError
from .observations import (
    interpretation_record,
    observation_record,
    observational_claim,
    observational_claim_pilot,
)
from .temporal import temporal_evidence


_SCHEMAS = {
    "ibm": "e7q.vendor.ibm/v1",
    "google": "e7q.vendor.google/v1",
}


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise E7QError(f"{field} must be an ISO 8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise E7QError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise E7QError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _number(value: Any, field: str, *, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise E7QError(f"{field} must be numeric")
    result = float(value)
    if result < minimum:
        raise E7QError(f"{field} must be at least {minimum:g}")
    return result


def _probability(value: Any, field: str) -> float:
    result = _number(value, field)
    if result > 1:
        raise E7QError(f"{field} must be between zero and one")
    return result


def _target(provider: str, raw: dict[str, Any]) -> dict[str, object]:
    required = {
        "name", "qubits", "topology", "native_gates", "available",
        "queue_depth", "single_qubit_error", "two_qubit_error", "readout_error",
    }
    missing = required - raw.keys()
    if missing:
        raise E7QError(f"vendor target missing: {', '.join(sorted(missing))}")
    topology = str(raw["topology"])
    if topology not in {"linear", "ring", "all-to-all"}:
        raise E7QError("topology must be linear, ring, or all-to-all")
    gates = raw["native_gates"]
    if not isinstance(gates, list) or not gates:
        raise E7QError("native_gates must be a non-empty list")
    qubits = int(_number(raw["qubits"], "qubits", minimum=1))
    queue_depth = int(_number(raw["queue_depth"], "queue_depth"))
    return {
        "name": str(raw["name"]),
        "qubits": qubits,
        "topology": topology,
        "native_gates": [str(gate).upper() for gate in gates],
        "available": bool(raw["available"]),
        "queue_depth": queue_depth,
        "single_qubit_error": _probability(
            raw["single_qubit_error"], "single_qubit_error"
        ),
        "two_qubit_error": _probability(
            raw["two_qubit_error"], "two_qubit_error"
        ),
        "readout_error": _probability(raw["readout_error"], "readout_error"),
        "provenance": {
            "provider": provider,
            "vendor_target": str(raw["name"]),
            "source": "user-supplied vendor export",
        },
    }


def ingest_vendor_export(
    provider: str,
    payload: dict[str, Any],
    *,
    max_age_hours: float | None = None,
    now: datetime | None = None,
    include_observational_claim_pilot: bool = False,
) -> dict[str, object]:
    """Normalize a supplied vendor export into e7q.calibration/v1."""
    provider = provider.lower()
    if provider not in _SCHEMAS:
        raise E7QError("provider must be ibm or google")
    if payload.get("schema") != _SCHEMAS[provider]:
        raise E7QError(f"{provider} export must use {_SCHEMAS[provider]}")
    captured = _timestamp(payload.get("captured_at"), "captured_at")
    validity_window: dict[str, object] = {
        "criterion": "maximum age from the supplied reference time",
        "maximum_age_hours": max_age_hours,
        "status": "not-evaluated",
    }
    if max_age_hours is not None:
        if max_age_hours < 0:
            raise E7QError("max_age_hours must be non-negative")
        reference = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        age_hours = (reference - captured).total_seconds() / 3600
        if age_hours < 0:
            raise E7QError("captured_at cannot be in the future")
        if age_hours > max_age_hours:
            raise E7QError(
                f"vendor export is stale ({age_hours:.1f}h > {max_age_hours:.1f}h)"
            )
        validity_window.update(
            {
                "age_hours": age_hours,
                "status": "within-window",
            }
        )
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise E7QError("vendor export requires at least one target")
    targets = []
    for raw in raw_targets:
        if not isinstance(raw, dict):
            raise E7QError("each vendor target must be an object")
        targets.append(_target(provider, raw))
    snapshot: dict[str, object] = {
        "schema": "e7q.calibration/v1",
        "captured_at": payload["captured_at"],
        "targets": targets,
        "temporal_evidence": temporal_evidence(
            temporal_order_roles=["TD0"],
            carrier_description="one supplied calibration snapshot",
            order_relation="single temporal observation",
            chronology_status="format-validated-not-authenticated",
            projection_from="user-supplied vendor calibration export",
            projection_to="normalized E7Q calibration snapshot",
            preserves=[
                "declared capture timestamp",
                "provider and source schema",
                "mapped target observations",
            ],
            loses=[
                "unmapped provider-native fields",
                "events between calibration snapshots",
                "provider-authenticated chronology",
            ],
            reconstruction_status="non-unique",
            reconstruction_limit=(
                "Several provider-native exports can normalize to the same "
                "E7Q calibration snapshot."
            ),
            clock={
                "field": "captured_at",
                "value": payload["captured_at"],
                "status": "format-validated-not-authenticated",
            },
            validity_window=validity_window,
            criterion_id="e7q.calibration-freshness",
            criterion_edition="1",
            criterion_parameters={"maximum_age_hours": max_age_hours},
            criterion="declared calibration freshness policy",
            phase=str(validity_window["status"]),
            boundary_crossing={"detected": False},
        ),
        "provenance": {
            "provider": provider,
            "source_schema": _SCHEMAS[provider],
            "source": "user-supplied vendor export",
            "network_access": False,
        },
    }
    if include_observational_claim_pilot:
        record_id = "observation:vendor-calibration-export"
        claim_id = "claim:reported-calibration-snapshot"
        limitations = [
            "provider identity and capture time were not authenticated",
            "normalization omits provider-native fields outside the E7Q mapping",
        ]
        unknowns = [
            "device changes before or after the captured snapshot",
            "unmapped provider-native calibration fields",
        ]
        interpretations = []
        if max_age_hours is not None:
            interpretations.append(
                interpretation_record(
                    interpretation_id="interpretation:calibration-freshness",
                    supporting_observation_claim_refs=[claim_id],
                    assumption_refs=["the supplied reference time is suitable for age evaluation"],
                    inference_rule_refs=["UTC timestamp subtraction"],
                    bridge_refs=["reported capture time to declared freshness policy"],
                    external_model_refs=[],
                    criterion_refs=["e7q.calibration-freshness@1"],
                    conclusion=(
                        f"{validity_window['status']} under the declared maximum age policy."
                    ),
                    inherited_limitations=limitations,
                    added_limitations=["freshness is not device-state validity"],
                    support_basis="mixed",
                    support_status="operationally-validated-offline",
                    admissible_use="screen the supplied snapshot by declared maximum age",
                    non_admissible_use=(
                        "provider authentication, current device-state certification, "
                        "or future calibration validity"
                    ),
                    validity_window=validity_window,
                    stop_or_reopen_condition=(
                        "reopen when the reference time, maximum age, or snapshot changes"
                    ),
                )
            )
        snapshot["observational_claim_pilot"] = observational_claim_pilot(
            pilot_id="e7q.calibration-ingestion",
            observation_records=[
                observation_record(
                    observation_id=record_id,
                    observer_ref=f"reported-provider:{provider}",
                    modelled_entity_ref=f"calibration-export:{payload['captured_at']}",
                    inquiry_profile_ref="e7q.calibration-normalization",
                    semantic_context_ref=_SCHEMAS[provider],
                    viewing_or_measurement_ref="supplied vendor calibration export",
                    observation_protocol_ref="e7q.calibration-ingestion/v1",
                    observed_at_or_during=payload["captured_at"],
                    temporal_support={
                        "captured_at": payload["captured_at"],
                        "status": "format-validated-not-authenticated",
                    },
                    spatial_or_population_support={
                        "provider": provider,
                        "targets": [target["name"] for target in targets],
                    },
                    resolution="mapped target-level calibration snapshot",
                    recorded_content={
                        "captured_at": payload["captured_at"],
                        "targets": targets,
                    },
                    provenance_refs=[_SCHEMAS[provider]],
                    evidence_refs=["user-supplied vendor export"],
                    known_limitations=limitations,
                    unknown_positions=unknowns,
                )
            ],
            observational_claims=[
                observational_claim(
                    claim_id=claim_id,
                    observation_record_refs=[record_id],
                    asserted_content=(
                        "The supplied vendor export reports the recorded capture time "
                        "and mapped target calibration values."
                    ),
                    evidence_path=[
                        "user-supplied vendor export",
                        "provider schema validation",
                        "E7Q target-field normalization",
                    ],
                    temporal_support={
                        "captured_at": payload["captured_at"],
                        "authenticated": False,
                    },
                    resolution="mapped target-level calibration snapshot",
                    known_limitations=limitations,
                    unknown_positions=unknowns,
                    blocked_overread=[
                        "the provider authenticated the export or timestamp",
                        "the snapshot describes the device outside its recorded instant",
                    ],
                )
            ],
            interpretations=interpretations,
        )
    return snapshot


def load_vendor_export(
    path: str | Path,
    provider: str,
    *,
    max_age_hours: float | None = None,
    include_observational_claim_pilot: bool = False,
) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise E7QError(f"invalid vendor export: {exc}") from exc
    if not isinstance(payload, dict):
        raise E7QError("vendor export must be an object")
    return ingest_vendor_export(
        provider,
        payload,
        max_age_hours=max_age_hours,
        include_observational_claim_pilot=include_observational_claim_pilot,
    )
