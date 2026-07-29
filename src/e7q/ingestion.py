# SPDX-License-Identifier: Apache-2.0
"""Offline vendor-export normalization for E7Q calibration snapshots."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .language import E7QError


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
) -> dict[str, object]:
    """Normalize a supplied vendor export into e7q.calibration/v1."""
    provider = provider.lower()
    if provider not in _SCHEMAS:
        raise E7QError("provider must be ibm or google")
    if payload.get("schema") != _SCHEMAS[provider]:
        raise E7QError(f"{provider} export must use {_SCHEMAS[provider]}")
    captured = _timestamp(payload.get("captured_at"), "captured_at")
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
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise E7QError("vendor export requires at least one target")
    targets = []
    for raw in raw_targets:
        if not isinstance(raw, dict):
            raise E7QError("each vendor target must be an object")
        targets.append(_target(provider, raw))
    return {
        "schema": "e7q.calibration/v1",
        "captured_at": payload["captured_at"],
        "targets": targets,
        "provenance": {
            "provider": provider,
            "source_schema": _SCHEMAS[provider],
            "source": "user-supplied vendor export",
            "network_access": False,
        },
    }


def load_vendor_export(
    path: str | Path,
    provider: str,
    *,
    max_age_hours: float | None = None,
) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise E7QError(f"invalid vendor export: {exc}") from exc
    if not isinstance(payload, dict):
        raise E7QError("vendor export must be an object")
    return ingest_vendor_export(
        provider, payload, max_age_hours=max_age_hours
    )
