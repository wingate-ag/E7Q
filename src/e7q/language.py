# SPDX-License-Identifier: Apache-2.0
"""Parser, simulator, verifier, comparison, and exporters for E7Q."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re

import numpy as np


class E7QError(ValueError):
    """Raised when an E7Q program is invalid."""


@dataclass(frozen=True)
class Operation:
    gate: str
    qubits: tuple[int, ...] = ()
    bits: tuple[int, ...] = ()
    condition: tuple[int, int] | None = None
    full_register: bool = False


@dataclass(frozen=True)
class Program:
    name: str
    shots: int
    backend: str
    seed: int | None
    qubits: int
    bits: int
    path: str
    operations: tuple[Operation, ...]
    allowed_outcomes: frozenset[str] | None
    require_normalized: bool


@dataclass(frozen=True)
class Execution:
    program: Program
    state: np.ndarray
    probabilities: dict[str, float]
    counts: dict[str, int]
    proof: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class Comparison:
    criterion: str
    equivalent: bool
    tolerance: float
    maximum_error: float
    global_phase: complex | None
    proof: tuple[dict[str, object], ...]


_ONE_QUBIT = {
    "X": np.array([[0, 1], [1, 0]], complex),
    "Y": np.array([[0, -1j], [1j, 0]], complex),
    "Z": np.array([[1, 0], [0, -1]], complex),
    "H": np.array([[1, 1], [1, -1]], complex) / math.sqrt(2),
    "S": np.array([[1, 0], [0, 1j]], complex),
    "T": np.array([[1, 0], [0, np.exp(1j * math.pi / 4)]], complex),
}
_TWO_QUBIT = {"CX", "CZ", "SWAP"}


def _strip_comments(source: str) -> str:
    return re.sub(r"(?m)//.*$|#.*$", "", source)


def _required(pattern: str, source: str, label: str) -> re.Match[str]:
    match = re.search(pattern, source, re.S)
    if not match:
        raise E7QError(f"missing or invalid {label}")
    return match


def parse(source: str) -> Program:
    """Parse E7Q source, including partial measurement and classical control."""
    text = _strip_comments(source)
    context = _required(r"context\s+(\w+)\s*\{(.*?)\}", text, "context")
    settings = dict(re.findall(r"(\w+)\s*:\s*([^\s}]+)", context.group(2)))
    try:
        shots = int(settings.get("shots", "1024"))
    except ValueError as exc:
        raise E7QError("shots must be an integer") from exc
    if shots < 1:
        raise E7QError("shots must be positive")
    backend = settings.get("backend", "statevector")
    if backend != "statevector":
        raise E7QError("only the statevector backend is supported")
    try:
        seed = int(settings["seed"]) if "seed" in settings else None
    except ValueError as exc:
        raise E7QError("seed must be an integer") from exc

    qreg = _required(r"(?m)^\s*qubits\s+(\w+)\[(\d+)\]", text, "qubit register")
    breg = _required(r"(?m)^\s*bits\s+(\w+)\[(\d+)\]", text, "bit register")
    qname, qubits = qreg.group(1), int(qreg.group(2))
    bname, bits = breg.group(1), int(breg.group(2))
    if qubits < 1 or bits < 1:
        raise E7QError("register sizes must be positive")

    path_match = _required(r"path\s+(\w+)\s*\{(.*?)\}", text, "path")
    path, body = path_match.groups()
    verify_match = _required(r"verify\s+(\w+)", text, "verify declaration")
    if verify_match.group(1) != path:
        raise E7QError("verify target does not match declared path")

    qref = rf"{re.escape(qname)}\[(\d+)\]"
    cref = rf"{re.escape(bname)}\[(\d+)\]"
    one_pattern = re.compile(rf"(X|Y|Z|H|S|T)\s+{qref}\Z")
    two_pattern = re.compile(rf"(CX|CZ|SWAP)\s+{qref}\s*,\s*{qref}\Z")
    partial_pattern = re.compile(rf"measure\s+{qref}\s*->\s*{cref}\Z")
    full_pattern = re.compile(
        rf"measure\s+{re.escape(qname)}\s*->\s*{re.escape(bname)}\Z"
    )
    condition_pattern = re.compile(
        rf"if\s+{cref}\s*==\s*([01])\s+(X|Y|Z|H|S|T)\s+{qref}\Z"
    )

    operations: list[Operation] = []
    full_measured = False
    for raw_statement in body.splitlines():
        statement = raw_statement.strip()
        if not statement:
            continue
        if full_measured:
            raise E7QError("full-register measurement must be the final operation")
        match = full_pattern.fullmatch(statement)
        if match:
            if bits < qubits:
                raise E7QError("full-register measurement requires bits >= qubits")
            operations.append(Operation("MEASURE", full_register=True))
            full_measured = True
            continue
        match = partial_pattern.fullmatch(statement)
        if match:
            qindex, bindex = map(int, match.groups())
            _validate_indices(qindex, bindex, qubits, bits, "measurement")
            operations.append(Operation("MEASURE", (qindex,), (bindex,)))
            continue
        match = condition_pattern.fullmatch(statement)
        if match:
            bindex, value, gate, qindex = match.groups()
            bindex, value, qindex = int(bindex), int(value), int(qindex)
            _validate_indices(qindex, bindex, qubits, bits, "condition")
            operations.append(Operation(gate, (qindex,), condition=(bindex, value)))
            continue
        match = two_pattern.fullmatch(statement) or one_pattern.fullmatch(statement)
        if not match:
            raise E7QError(f"invalid path statement: {statement}")
        gate = match.group(1)
        indices = tuple(int(value) for value in match.groups()[1:])
        if any(index >= qubits for index in indices):
            raise E7QError(f"{gate} qubit index out of range")
        if len(indices) == 2 and indices[0] == indices[1]:
            raise E7QError(f"{gate} requires distinct qubits")
        operations.append(Operation(gate, indices))
    if not any(operation.gate == "MEASURE" for operation in operations):
        raise E7QError("path must contain measurement")

    require_normalized = bool(re.search(r"invariant\s+normalized\b", text))
    outcomes = re.search(r"invariant\s+outcomes\s+in\s*\{([^}]+)\}", text)
    allowed = None
    if outcomes:
        allowed = frozenset(item.strip() for item in outcomes.group(1).split(","))
        if any(len(item) != bits or set(item) - {"0", "1"} for item in allowed):
            raise E7QError("outcome invariants must be classical-register-width bit strings")
    return Program(
        context.group(1), shots, backend, seed, qubits, bits, path,
        tuple(operations), allowed, require_normalized,
    )


def _validate_indices(qindex: int, bindex: int, qubits: int, bits: int, label: str) -> None:
    if qindex >= qubits:
        raise E7QError(f"{label} qubit index out of range")
    if bindex >= bits:
        raise E7QError(f"{label} bit index out of range")


def _apply_one(state: np.ndarray, gate: np.ndarray, target: int, size: int) -> np.ndarray:
    tensor = state.reshape((2,) * size)
    moved = np.moveaxis(tensor, target, 0)
    transformed = np.tensordot(gate, moved, axes=([1], [0]))
    return np.moveaxis(transformed, 0, target).reshape(-1)


def _apply_two(state: np.ndarray, gate: str, first: int, second: int, size: int) -> np.ndarray:
    output = np.zeros_like(state)
    for index, amplitude in enumerate(state):
        values = list(f"{index:0{size}b}")
        a, b = int(values[first]), int(values[second])
        if gate == "CX" and a:
            values[second] = str(1 - b)
        elif gate == "CZ" and a and b:
            amplitude = -amplitude
        elif gate == "SWAP":
            values[first], values[second] = values[second], values[first]
        output[int("".join(values), 2)] += amplitude
    return output


def _measure_qubit(
    state: np.ndarray, target: int, size: int, rng: np.random.Generator
) -> tuple[np.ndarray, int, float]:
    mask = np.array([int(f"{index:0{size}b}"[target]) for index in range(len(state))])
    p_one = float(np.sum(np.abs(state[mask == 1]) ** 2))
    outcome = int(rng.random() < p_one)
    collapsed = state.copy()
    collapsed[mask != outcome] = 0
    probability = p_one if outcome else 1 - p_one
    if probability <= 1e-15:
        raise E7QError("measurement selected a zero-probability branch")
    collapsed /= math.sqrt(probability)
    return collapsed, outcome, probability


def _is_dynamic(program: Program) -> bool:
    return any(
        operation.condition is not None
        or (operation.gate == "MEASURE" and not operation.full_register)
        for operation in program.operations
    )


def _initial_state(program: Program) -> np.ndarray:
    state = np.zeros(2**program.qubits, complex)
    state[0] = 1
    return state


def run(program: Program) -> Execution:
    """Execute a program; dynamic paths are evaluated shot by shot."""
    if not _is_dynamic(program):
        return _run_unitary(program)

    rng = np.random.default_rng(program.seed)
    counts: dict[str, int] = {}
    stats = [
        {"executed": 0, "skipped": 0, "outcomes": {"0": 0, "1": 0}}
        for _ in program.operations
    ]
    final_state = _initial_state(program)
    for _ in range(program.shots):
        state = _initial_state(program)
        classical = [0] * program.bits
        for index, operation in enumerate(program.operations):
            if operation.condition is not None:
                bit, value = operation.condition
                if classical[bit] != value:
                    stats[index]["skipped"] += 1
                    continue
            stats[index]["executed"] += 1
            if operation.gate == "MEASURE":
                if operation.full_register:
                    for qindex in range(program.qubits):
                        state, outcome, _ = _measure_qubit(
                            state, qindex, program.qubits, rng
                        )
                        classical[qindex] = outcome
                else:
                    state, outcome, _ = _measure_qubit(
                        state, operation.qubits[0], program.qubits, rng
                    )
                    classical[operation.bits[0]] = outcome
                    stats[index]["outcomes"][str(outcome)] += 1
            elif operation.gate in _ONE_QUBIT:
                state = _apply_one(
                    state, _ONE_QUBIT[operation.gate],
                    operation.qubits[0], program.qubits,
                )
            else:
                state = _apply_two(
                    state, operation.gate, *operation.qubits, program.qubits
                )
        label = "".join(map(str, classical))
        counts[label] = counts.get(label, 0) + 1
        final_state = state

    probabilities = {
        label: count / program.shots for label, count in sorted(counts.items())
    }
    proof: list[dict[str, object]] = [{
        "step": 0, "kind": "initialize", "shots": program.shots, "state_norm": 1.0
    }]
    for operation, stat in zip(program.operations, stats):
        if operation.gate == "MEASURE":
            item = {
                "step": len(proof), "kind": "project", "operator": "measure",
                "qubits": list(operation.qubits), "bits": list(operation.bits),
                "full_register": operation.full_register,
                "executed": stat["executed"],
            }
            if not operation.full_register:
                item["outcomes"] = stat["outcomes"]
        else:
            item = {
                "step": len(proof), "kind": "conditional-transform"
                if operation.condition else "transform",
                "operator": operation.gate, "qubits": list(operation.qubits),
                "executed": stat["executed"], "skipped": stat["skipped"],
            }
            if operation.condition:
                item["condition"] = {
                    "bit": operation.condition[0], "equals": operation.condition[1]
                }
        proof.append(item)
    proof.append({
        "step": len(proof), "kind": "result", "shots": program.shots,
        "outcomes": counts,
    })
    return Execution(program, final_state, probabilities, counts, tuple(proof))


def _run_unitary(program: Program) -> Execution:
    state = _initial_state(program)
    proof: list[dict[str, object]] = [
        {"step": 0, "kind": "initialize", "state_norm": 1.0}
    ]
    for operation in program.operations:
        if operation.gate == "MEASURE":
            continue
        if operation.gate in _ONE_QUBIT:
            state = _apply_one(
                state, _ONE_QUBIT[operation.gate], operation.qubits[0], program.qubits
            )
        else:
            state = _apply_two(state, operation.gate, *operation.qubits, program.qubits)
        proof.append({
            "step": len(proof), "kind": "transform", "operator": operation.gate,
            "qubits": list(operation.qubits),
            "state_norm": float(np.vdot(state, state).real),
        })
    raw = np.abs(state) ** 2
    qlabels = [f"{index:0{program.qubits}b}" for index in range(len(raw))]
    labels = [label + "0" * (program.bits - program.qubits) for label in qlabels]
    probabilities = {
        label: float(value) for label, value in zip(labels, raw) if value > 1e-15
    }
    rng = np.random.default_rng(program.seed)
    samples = rng.choice(labels, size=program.shots, p=raw)
    counts = {
        label: int(np.count_nonzero(samples == label)) for label in labels
        if np.count_nonzero(samples == label)
    }
    proof.append({
        "step": len(proof), "kind": "project", "operator": "measure",
        "shots": program.shots, "outcomes": counts,
    })
    return Execution(program, state, probabilities, counts, tuple(proof))


def circuit_unitary(program: Program) -> np.ndarray:
    """Return a circuit unitary, rejecting non-unitary dynamic paths."""
    if _is_dynamic(program):
        raise E7QError(
            "unitary comparison does not support mid-circuit measurement or classical control"
        )
    dimension = 2**program.qubits
    columns: list[np.ndarray] = []
    for basis in range(dimension):
        state = np.zeros(dimension, complex)
        state[basis] = 1
        for operation in program.operations:
            if operation.gate == "MEASURE":
                continue
            if operation.gate in _ONE_QUBIT:
                state = _apply_one(
                    state, _ONE_QUBIT[operation.gate],
                    operation.qubits[0], program.qubits,
                )
            else:
                state = _apply_two(
                    state, operation.gate, *operation.qubits, program.qubits
                )
        columns.append(state)
    return np.column_stack(columns)


def compare(
    first: Program, second: Program, criterion: str = "global-phase",
    tolerance: float = 1e-12,
) -> Comparison:
    criteria = {"exact", "global-phase", "measurement", "tolerance"}
    if criterion not in criteria:
        raise E7QError(f"unknown equivalence criterion: {criterion}")
    if tolerance <= 0:
        raise E7QError("comparison tolerance must be positive")
    if first.qubits != second.qubits:
        raise E7QError("circuits must have the same number of qubits")
    left, right = circuit_unitary(first), circuit_unitary(second)
    phase: complex | None = None
    if criterion == "measurement":
        error = float(np.max(np.abs(np.abs(left) ** 2 - np.abs(right) ** 2)))
    elif criterion == "global-phase":
        overlap = np.vdot(left.reshape(-1), right.reshape(-1))
        if abs(overlap) > tolerance:
            phase = overlap / abs(overlap)
        adjusted = right / phase if phase is not None else right
        error = float(np.max(np.abs(left - adjusted)))
    else:
        error = float(np.max(np.abs(left - right)))
    threshold = tolerance if criterion != "exact" else 0.0
    equivalent = error <= threshold
    proof = ({
        "step": 0, "kind": "compare", "left": first.name, "right": second.name,
        "criterion": criterion, "qubits": first.qubits,
    }, {
        "step": 1, "kind": "equivalence", "equivalent": equivalent,
        "maximum_error": error, "tolerance": threshold,
        "global_phase": (
            {"real": float(phase.real), "imag": float(phase.imag)}
            if phase is not None else None
        ),
    })
    return Comparison(criterion, equivalent, threshold, error, phase, proof)


def comparison_result(comparison: Comparison) -> dict[str, object]:
    return {
        "status": "PASS" if comparison.equivalent else "FAIL",
        "criterion": comparison.criterion, "equivalent": comparison.equivalent,
        "maximum_error": comparison.maximum_error,
        "tolerance": comparison.tolerance,
        "global_phase": (
            {"real": float(comparison.global_phase.real),
             "imag": float(comparison.global_phase.imag)}
            if comparison.global_phase is not None else None
        ),
        "proof": list(comparison.proof),
    }


def verify(execution: Execution, tolerance: float = 1e-12) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    if execution.program.require_normalized:
        norm = float(np.vdot(execution.state, execution.state).real)
        checks.append({"name": "normalized", "passed": abs(norm - 1.0) <= tolerance})
    if execution.program.allowed_outcomes is not None:
        observed = {key for key, value in execution.probabilities.items() if value > tolerance}
        checks.append({
            "name": "outcomes", "passed": observed <= execution.program.allowed_outcomes,
            "allowed": sorted(execution.program.allowed_outcomes),
            "observed": sorted(observed),
        })
    return {
        "status": "PASS" if all(check["passed"] for check in checks) else "FAIL",
        "checks": checks, "probabilities": execution.probabilities,
        "counts": execution.counts, "proof": list(execution.proof),
    }


def proof_json(result: dict[str, object]) -> str:
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


def openqasm(program: Program) -> str:
    lines = [
        "OPENQASM 3.0;", 'include "stdgates.inc";',
        f"qubit[{program.qubits}] q;", f"bit[{program.bits}] c;",
    ]
    names = {"CX": "cx", "CZ": "cz", "SWAP": "swap"}
    for operation in program.operations:
        if operation.gate == "MEASURE":
            if operation.full_register:
                lines.append("c = measure q;")
            else:
                lines.append(
                    f"c[{operation.bits[0]}] = measure q[{operation.qubits[0]}];"
                )
            continue
        gate = operation.gate.lower() if len(operation.qubits) == 1 else names[operation.gate]
        refs = ", ".join(f"q[{index}]" for index in operation.qubits)
        statement = f"{gate} {refs};"
        if operation.condition:
            bit, value = operation.condition
            statement = f"if (c[{bit}] == {value}) {statement}"
        lines.append(statement)
    return "\n".join(lines) + "\n"


def load(path: str | Path) -> Program:
    return parse(Path(path).read_text(encoding="utf-8"))
