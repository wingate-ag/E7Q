# SPDX-License-Identifier: Apache-2.0
"""Offline calibration snapshots and auditable target selection."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .language import E7QError, Program
from .planning import Plan, plan, plan_result


@dataclass(frozen=True)
class Candidate:
    name: str
    score: float
    queue_depth: int
    plan: Plan
    evidence: dict[str, object]


def load_snapshot(path: str | Path) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise E7QError(f"invalid calibration snapshot: {exc}") from exc
    if value.get("schema") != "e7q.calibration/v1":
        raise E7QError("calibration snapshot must use e7q.calibration/v1")
    if not isinstance(value.get("captured_at"), str):
        raise E7QError("calibration snapshot requires captured_at")
    if not isinstance(value.get("targets"), list) or not value["targets"]:
        raise E7QError("calibration snapshot requires at least one target")
    return value


def _probability(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
        raise E7QError(f"{field} must be between zero and one")
    return float(value)


def _candidate(program: Program, target: dict[str, object]) -> Candidate:
    required = {
        "name", "qubits", "topology", "native_gates", "available",
        "queue_depth", "single_qubit_error", "two_qubit_error", "readout_error",
    }
    missing = required - target.keys()
    if missing:
        raise E7QError(f"calibration target missing: {', '.join(sorted(missing))}")
    name = str(target["name"])
    qubits = int(target["qubits"])
    queue = int(target["queue_depth"])
    if qubits < program.qubits:
        raise E7QError(f"{name}: insufficient qubits")
    if queue < 0:
        raise E7QError(f"{name}: queue_depth must be non-negative")
    if not target["available"]:
        raise E7QError(f"{name}: target unavailable")
    native = frozenset(str(gate).upper() for gate in target["native_gates"])
    planned = plan(program, str(target["topology"]), native)
    result = plan_result(planned)
    counts = planned.compiled.gate_counts
    one_count = sum(
        count for gate, count in counts.items()
        if gate not in {"CX", "CZ", "SWAP", "MEASURE"}
    )
    two_count = planned.compiled.two_qubit_gates
    measured = program.qubits if counts.get("MEASURE", 0) else 0
    one_error = _probability(target["single_qubit_error"], "single_qubit_error")
    two_error = _probability(target["two_qubit_error"], "two_qubit_error")
    readout_error = _probability(target["readout_error"], "readout_error")
    score = (
        (1 - one_error) ** one_count
        * (1 - two_error) ** two_count
        * (1 - readout_error) ** measured
    )
    evidence = {
        "name": name,
        "compatible": True,
        "score": score,
        "queue_depth": queue,
        "compiled": result["compiled"],
        "overhead": result["overhead"],
        "observed": {
            "captured_qubits": qubits,
            "topology": target["topology"],
            "native_gates": sorted(native),
            "single_qubit_error": one_error,
            "two_qubit_error": two_error,
            "readout_error": readout_error,
        },
        "estimated": {
            "single_qubit_gates": one_count,
            "two_qubit_gates": two_count,
            "measured_qubits": measured,
            "success_proxy": score,
        },
    }
    return Candidate(name, score, queue, planned, evidence)


def select_target(program: Program, snapshot: dict[str, object]) -> dict[str, object]:
    candidates: list[Candidate] = []
    rejected: list[dict[str, str]] = []
    for raw in snapshot["targets"]:
        if not isinstance(raw, dict):
            raise E7QError("each calibration target must be an object")
        try:
            candidates.append(_candidate(program, raw))
        except E7QError as exc:
            rejected.append({"name": str(raw.get("name", "<unnamed>")), "reason": str(exc)})
    if not candidates:
        raise E7QError("no compatible targets in calibration snapshot")
    candidates.sort(key=lambda item: (-item.score, item.queue_depth, item.name))
    selected = candidates[0]
    ranking = [candidate.evidence for candidate in candidates]
    proof = [
        {
            "step": 0,
            "kind": "calibration-snapshot",
            "schema": snapshot["schema"],
            "captured_at": snapshot["captured_at"],
            "source": "user-supplied snapshot",
        },
        {
            "step": 1,
            "kind": "target-ranking",
            "criterion": "success proxy descending, queue depth ascending, name ascending",
            "candidates": ranking,
            "rejected": rejected,
        },
        {
            "step": 2,
            "kind": "target-selection",
            "selected": selected.name,
            "score": selected.score,
            "boundary": (
                "Ranking is an estimate from supplied snapshot values; it is not "
                "live calibration, job submission, cost, or guaranteed fidelity."
            ),
        },
    ]
    return {
        "status": "PASS",
        "selected": selected.name,
        "score": selected.score,
        "captured_at": snapshot["captured_at"],
        "ranking": ranking,
        "rejected": rejected,
        "proof": proof,
    }
