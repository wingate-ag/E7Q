# SPDX-License-Identifier: Apache-2.0
"""Reproducible, provider-neutral execution bundles."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from .calibration import select_target
from .language import E7QError, Program, openqasm
from .planning import plan, plan_result


def _digest(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def build_execution_bundle(
    program: Program,
    source: bytes,
    snapshot: dict[str, object],
    *,
    shots: int = 1000,
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
    return {
        "schema": "e7q.execution-bundle/v1",
        "status": "READY",
        "submitted": False,
        "target": selected_name,
        "shots": shots,
        "captured_at": snapshot["captured_at"],
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
