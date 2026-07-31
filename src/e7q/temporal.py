# SPDX-License-Identifier: Apache-2.0
"""Bounded temporal-evidence records for E7Q offline artifacts."""
from __future__ import annotations

from typing import Any


SCHEMA = "e7q.temporal-evidence/v1"

_CARRIERS = {f"TD{index}" for index in range(8)}
_CHRONOLOGY_STATUSES = {
    "not-applicable",
    "not-established",
    "proof-order-only",
    "declared-not-authenticated",
    "format-validated-not-authenticated",
    "provider-reported-not-authenticated",
    "authenticated",
}
_RECONSTRUCTION_STATUSES = {
    "not-attempted",
    "non-unique",
    "partial",
    "unique-under-declared-model",
}


def temporal_evidence(
    *,
    carrier: str,
    carrier_description: str,
    order_relation: str,
    chronology_status: str,
    projection_from: str,
    projection_to: str,
    preserves: list[str],
    loses: list[str],
    reconstruction_status: str,
    reconstruction_limit: str,
    clock: dict[str, object] | None = None,
    validity_window: dict[str, object] | None = None,
    criterion: str | None = None,
    phase: str | None = None,
    boundary_crossing: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a deterministic E7Q temporal-evidence subrecord."""
    value: dict[str, object] = {
        "schema": SCHEMA,
        "carrier": carrier,
        "carrier_description": carrier_description,
        "order_relation": order_relation,
        "chronology_status": chronology_status,
        "projection": {
            "from": projection_from,
            "to": projection_to,
            "preserves": preserves,
            "loses": loses,
        },
        "reconstruction": {
            "status": reconstruction_status,
            "limit": reconstruction_limit,
        },
    }
    if clock is not None:
        value["clock"] = clock
    if validity_window is not None:
        value["validity_window"] = validity_window
    if criterion is not None or phase is not None:
        value["temporal_phase"] = {
            "criterion": criterion,
            "status": phase,
        }
    if boundary_crossing is not None:
        value["boundary_crossing"] = boundary_crossing
    return value


def conformance_checks(value: Any) -> list[dict[str, object]]:
    """Return structural checks for an embedded temporal-evidence record."""

    def check(name: str, passed: bool) -> dict[str, object]:
        return {"name": f"temporal-evidence:{name}", "passed": passed}

    if not isinstance(value, dict):
        return [check("object", False)]

    projection = value.get("projection")
    reconstruction = value.get("reconstruction")
    checks = [
        check("schema", value.get("schema") == SCHEMA),
        check("carrier", value.get("carrier") in _CARRIERS),
        check(
            "carrier-description",
            isinstance(value.get("carrier_description"), str)
            and bool(value["carrier_description"]),
        ),
        check(
            "order-relation",
            isinstance(value.get("order_relation"), str)
            and bool(value["order_relation"]),
        ),
        check(
            "chronology-status",
            value.get("chronology_status") in _CHRONOLOGY_STATUSES,
        ),
        check("projection", isinstance(projection, dict)),
        check("reconstruction", isinstance(reconstruction, dict)),
    ]
    if isinstance(projection, dict):
        checks.extend(
            [
                check(
                    "projection-from",
                    isinstance(projection.get("from"), str)
                    and bool(projection["from"]),
                ),
                check(
                    "projection-to",
                    isinstance(projection.get("to"), str)
                    and bool(projection["to"]),
                ),
                check(
                    "projection-preserves",
                    isinstance(projection.get("preserves"), list),
                ),
                check(
                    "projection-loses",
                    isinstance(projection.get("loses"), list),
                ),
            ]
        )
    if isinstance(reconstruction, dict):
        checks.extend(
            [
                check(
                    "reconstruction-status",
                    reconstruction.get("status") in _RECONSTRUCTION_STATUSES,
                ),
                check(
                    "reconstruction-limit",
                    isinstance(reconstruction.get("limit"), str)
                    and bool(reconstruction["limit"]),
                ),
            ]
        )
    clock = value.get("clock")
    if clock is not None:
        checks.append(check("clock", isinstance(clock, dict)))
        if isinstance(clock, dict):
            checks.extend(
                [
                    check(
                        "clock-field",
                        isinstance(clock.get("field"), str) and bool(clock["field"]),
                    ),
                    check(
                        "clock-status",
                        clock.get("status") in _CHRONOLOGY_STATUSES,
                    ),
                ]
            )
    temporal_phase = value.get("temporal_phase")
    if temporal_phase is not None:
        checks.append(check("phase", isinstance(temporal_phase, dict)))
        if isinstance(temporal_phase, dict):
            checks.extend(
                [
                    check(
                        "phase-criterion",
                        isinstance(temporal_phase.get("criterion"), str)
                        and bool(temporal_phase["criterion"]),
                    ),
                    check(
                        "phase-status",
                        isinstance(temporal_phase.get("status"), str)
                        and bool(temporal_phase["status"]),
                    ),
                ]
            )
    crossing = value.get("boundary_crossing")
    if crossing is not None:
        checks.append(check("boundary-crossing", isinstance(crossing, dict)))
        if isinstance(crossing, dict):
            checks.append(
                check("boundary-detected", isinstance(crossing.get("detected"), bool))
            )
    if (
        value.get("chronology_status") == "authenticated"
        or isinstance(clock, dict)
        and clock.get("status") == "authenticated"
    ):
        authentication = value.get("authentication")
        checks.append(
            check(
                "chronology-authentication",
                isinstance(authentication, dict)
                and isinstance(authentication.get("evidence_ref"), str)
                and bool(authentication["evidence_ref"]),
            )
        )
    return checks
