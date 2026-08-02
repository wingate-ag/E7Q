# SPDX-License-Identifier: Apache-2.0
"""Reproducible, provider-neutral execution bundles."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from .calibration import select_target
from .language import E7QError, Program, openqasm
from .orientation import temporal_orientation_pilot
from .planning import plan, plan_result
from .temporal import temporal_evidence


def _digest(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def build_execution_bundle(
    program: Program,
    source: bytes,
    snapshot: dict[str, object],
    *,
    shots: int = 1000,
    include_temporal_orientation_pilot: bool = False,
) -> dict[str, object]:
    """Build an offline handoff bundle without submitting a hardware job."""
    if shots < 1:
        raise E7QError("shots must be at least one")
    selection = select_target(program, snapshot)
    selected_name = str(selection["selected"])
    target = next(
        (
            item for item in snapshot["targets"]
            if isinstance(item, dict) and str(item.get("name")) == selected_name
        ),
        None,
    )
    if target is None:
        raise E7QError("selected target is missing from calibration snapshot")
    native = frozenset(str(gate).upper() for gate in target["native_gates"])
    planned = plan(program, str(target["topology"]), native)
    planning = plan_result(planned)
    qasm = openqasm(planned.compilation.program)
    snapshot_bytes = (
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    proof = [
        {
            "step": 0,
            "kind": "input-identity",
            "source_digest": _digest(source),
            "snapshot_digest": _digest(snapshot_bytes),
            "captured_at": snapshot["captured_at"],
        },
        {
            "step": 1,
            "kind": "target-selection",
            "selected": selected_name,
            "score": selection["score"],
            "criterion": "calibration snapshot selection policy",
        },
        {
            "step": 2,
            "kind": "compile",
            "target": selected_name,
            "compiled": planning["compiled"],
            "overhead": planning["overhead"],
            "openqasm_digest": _digest(qasm.encode("utf-8")),
        },
        {
            "step": 3,
            "kind": "handoff-boundary",
            "status": "READY",
            "submitted": False,
            "boundary": (
                "Offline execution bundle only; no credentials were used, no job "
                "was submitted, and no execution, cost, or fidelity result is claimed."
            ),
        },
    ]
    bundle: dict[str, object] = {
        "schema": "e7q.execution-bundle/v1",
        "status": "READY",
        "submitted": False,
        "target": selected_name,
        "shots": shots,
        "captured_at": snapshot["captured_at"],
        "temporal_evidence": temporal_evidence(
            temporal_order_roles=["TD1"],
            carrier_description="ordered preparation and offline handoff path",
            order_relation="Proof-of-Path step order",
            chronology_status="proof-order-only",
            projection_from="program plus supplied calibration snapshot",
            projection_to="routed offline execution bundle",
            preserves=[
                "program and snapshot digests",
                "target-selection decision",
                "compilation and handoff order",
            ],
            loses=[
                "runtime queue history",
                "submission and execution events",
                "physical-device state evolution",
            ],
            reconstruction_status="partial",
            reconstruction_limit=(
                "The bundle identifies inputs by digest but does not contain "
                "submission or physical execution history."
            ),
            clock={
                "field": "captured_at",
                "value": snapshot["captured_at"],
                "status": "declared-not-authenticated",
            },
            criterion_id="e7q.offline-handoff-readiness",
            criterion_edition="1",
            criterion_parameters={},
            criterion="offline handoff readiness",
            phase="READY",
            boundary_crossing={"detected": False},
        ),
        "source_digest": _digest(source),
        "snapshot_digest": _digest(snapshot_bytes),
        "openqasm": qasm,
        "openqasm_digest": _digest(qasm.encode("utf-8")),
        "planning": {
            "compiled": planning["compiled"],
            "overhead": planning["overhead"],
        },
        "selection": {
            "score": selection["score"],
            "ranking": selection["ranking"],
            "rejected": selection["rejected"],
        },
        "proof": proof,
    }
    if include_temporal_orientation_pilot:
        bundle["temporal_orientation_pilot"] = temporal_orientation_pilot(
            pilot_id="e7q.execution-bundle",
            orientation_ref="program-to-offline-handoff Proof-of-Path order",
            observer_temporal_locality_ref="offline handoff boundary after compilation",
            directional_relation_kinds=["sequence", "dependency", "globalConsistency"],
            reverse_representation_ref="handoff-to-input reverse proof traversal",
            preserved_under_reversal=[
                "proof-step membership",
                "source, snapshot, and OpenQASM identity digests",
            ],
            reversed_hidden_or_unsupported=[
                "Proof-of-Path step order",
                "submission, execution, and physical causation",
            ],
            time_reversal_symmetry_status="not-assessed",
            causal_reversal_status="unsupported",
            final_constraint_refs=["offline handoff readiness criterion"],
            global_consistency_refs=["source, snapshot, and OpenQASM digest linkage"],
            history_whole_ref="one preparation-and-handoff Proof-of-Path",
            clock_or_synchronisation_model_ref="snapshot captured_at field; unauthenticated",
            accumulated_valid_record_ref="execution bundle proof",
            compatible_history_family_ref="temporal_evidence.reconstruction",
            fixed_condition_refs=[
                "program source bytes",
                "calibration snapshot",
                "target-selection policy",
                "compiler and planner rules",
            ],
            excluded_history_refs=[],
            exclusion_meaning=(
                "incompatibility with the bundle digests and proof path, not "
                "destruction or nonexistence"
            ),
            correction_or_retraction_refs=[],
            interaction_rule_refs=[],
            narrowing_status="not-claimed",
            decision_effect=(
                "permits reverse audit traversal while blocking claims that the "
                "preparation process or physical causation ran backwards"
            ),
        )
    return bundle
