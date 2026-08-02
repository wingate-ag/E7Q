# SPDX-License-Identifier: Apache-2.0
"""Bounded temporal-evidence records for E7Q offline artifacts."""
from __future__ import annotations

from typing import Any


SCHEMA = "e7q.temporal-evidence/v2"
LEGACY_SCHEMA = "e7q.temporal-evidence/v1"

_ORDER_ROLES = {f"TD{index}" for index in range(8)}
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
    temporal_order_roles: list[str] | None = None,
    carrier_ref: str | None = None,
    carrier: str | None = None,
    criterion_id: str | None = None,
    criterion_edition: str | None = None,
    criterion_parameters: dict[str, object] | None = None,
    criterion: str | None = None,
    phase: str | None = None,
    boundary_crossing: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a deterministic E7Q temporal-evidence subrecord.

    ``carrier`` remains as a compatibility alias for one TD0--TD7 order role.
    It is not emitted as a carrier: E7G-T v0.11 distinguishes temporal
    carriers from the TD order roles used to describe them.
    """
    order_roles = list(temporal_order_roles or ([] if carrier is None else [carrier]))
    value: dict[str, object] = {
        "schema": SCHEMA,
        "temporal_order_roles": order_roles,
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
    if carrier_ref is not None:
        value["carrier_ref"] = carrier_ref
    if clock is not None:
        value["clock"] = clock
    if validity_window is not None:
        value["validity_window"] = validity_window
    if criterion_id is not None or criterion is not None or phase is not None:
        temporal_phase: dict[str, object] = {
            "criterion_id": criterion_id,
            "criterion_edition": criterion_edition,
            "parameters": criterion_parameters or {},
            "status": phase,
        }
        if criterion is not None:
            temporal_phase["description"] = criterion
        value["temporal_phase"] = temporal_phase
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
    schema = value.get("schema")
    checks = [
        check("schema", schema in {SCHEMA, LEGACY_SCHEMA}),
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
    if schema == LEGACY_SCHEMA:
        checks.append(check("carrier", value.get("carrier") in _ORDER_ROLES))
    else:
        order_roles = value.get("temporal_order_roles")
        checks.append(
            check(
                "order-roles",
                isinstance(order_roles, list)
                and bool(order_roles)
                and len(set(order_roles)) == len(order_roles)
                and all(role in _ORDER_ROLES for role in order_roles),
            )
        )
        carrier_ref = value.get("carrier_ref")
        if carrier_ref is not None:
            checks.append(
                check(
                    "carrier-ref",
                    isinstance(carrier_ref, str) and bool(carrier_ref),
                )
            )
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
            if schema == LEGACY_SCHEMA:
                checks.append(
                    check(
                        "phase-criterion",
                        isinstance(temporal_phase.get("criterion"), str)
                        and bool(temporal_phase["criterion"]),
                    )
                )
            else:
                checks.extend(
                    [
                        check(
                            "phase-criterion-id",
                            isinstance(temporal_phase.get("criterion_id"), str)
                            and bool(temporal_phase["criterion_id"]),
                        ),
                        check(
                            "phase-criterion-edition",
                            isinstance(temporal_phase.get("criterion_edition"), str)
                            and bool(temporal_phase["criterion_edition"]),
                        ),
                        check(
                            "phase-parameters",
                            isinstance(temporal_phase.get("parameters"), dict),
                        ),
                    ]
                )
            checks.append(
                check(
                    "phase-status",
                    isinstance(temporal_phase.get("status"), str)
                    and bool(temporal_phase["status"]),
                )
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
