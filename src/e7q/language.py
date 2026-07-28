# SPDX-License-Identifier: Apache-2.0
"""Parser, state-vector executor, verifier, and exporters for E7Q v0.1."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
from typing import Iterable

import numpy as np


class E7QError(ValueError):
    """Raised when an E7Q program is invalid."""


@dataclass(frozen=True)
class Operation:
    gate: str
    qubits: tuple[int, ...] = ()


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
    """Parse the intentionally small E7Q v0.1 syntax."""
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
        raise E7QError("v0.1 supports only the statevector backend")
    try:
        seed = int(settings["seed"]) if "seed" in settings else None
    except ValueError as exc:
        raise E7QError("seed must be an integer") from exc

    qreg = _required(r"(?m)^\s*qubits\s+(\w+)\[(\d+)\]", text, "qubit register")
    breg = _required(r"(?m)^\s*bits\s+(\w+)\[(\d+)\]", text, "bit register")
    qname, qubits = qreg.group(1), int(qreg.group(2))
    bname, bits = breg.group(1), int(breg.group(2))
    if qubits < 1 or bits < qubits:
        raise E7QError("register sizes require qubits >= 1 and bits >= qubits")

    path_match = _required(r"path\s+(\w+)\s*\{(.*?)\}", text, "path")
    path, body = path_match.groups()
    verify_match = _required(r"verify\s+(\w+)", text, "verify declaration")
    if verify_match.group(1) != path:
        raise E7QError("verify target does not match declared path")

    operations: list[Operation] = []
    measured = False
    one_pattern = re.compile(rf"(X|Y|Z|H|S|T)\s+{re.escape(qname)}\[(\d+)\]\Z")
    two_pattern = re.compile(
        rf"(CX|CZ|SWAP)\s+{re.escape(qname)}\[(\d+)\]\s*,\s*"
        rf"{re.escape(qname)}\[(\d+)\]\Z"
    )
    measure_pattern = re.compile(
        rf"measure\s+{re.escape(qname)}\s*->\s*{re.escape(bname)}\Z"
    )
    for raw_statement in body.splitlines():
        statement = raw_statement.strip()
        if not statement:
            continue
        if statement.startswith("measure"):
            if not measure_pattern.fullmatch(statement):
                raise E7QError(f"invalid path statement: {statement}")
            if measured:
                raise E7QError("only one terminal measurement is supported")
            operations.append(Operation("MEASURE"))
            measured = True
            continue
        if measured:
            raise E7QError("measurement must be the final operation")
        matched = two_pattern.fullmatch(statement) or one_pattern.fullmatch(statement)
        if not matched:
            raise E7QError(f"invalid path statement: {statement}")
        gate = matched.group(1)
        indices = tuple(int(value) for value in matched.groups()[1:])
        if any(index >= qubits for index in indices):
            raise E7QError(f"{gate} qubit index out of range")
        if len(indices) == 2 and indices[0] == indices[1]:
            raise E7QError(f"{gate} requires distinct qubits")
        operations.append(Operation(gate, indices))
    if not measured:
        raise E7QError("path must end with measurement")

    require_normalized = bool(re.search(r"invariant\s+normalized\b", text))
    outcomes = re.search(r"invariant\s+outcomes\s+in\s*\{([^}]+)\}", text)
    allowed = None
    if outcomes:
        allowed = frozenset(item.strip() for item in outcomes.group(1).split(","))
        if any(len(item) != qubits or set(item) - {"0", "1"} for item in allowed):
            raise E7QError("outcome invariants must be qubit-width bit strings")
    return Program(
        context.group(1), shots, backend, seed, qubits, bits, path,
        tuple(operations), allowed, require_normalized,
    )


def _apply_one(state: np.ndarray, gate: np.ndarray, target: int, size: int) -> np.ndarray:
    tensor = state.reshape((2,) * size)
    moved = np.moveaxis(tensor, target, 0)
    transformed = np.tensordot(gate, moved, axes=([1], [0]))
    return np.moveaxis(transformed, 0, target).reshape(-1)


def _apply_two(state: np.ndarray, gate: str, first: int, second: int, size: int) -> np.ndarray:
    output = np.zeros_like(state)
    for index, amplitude in enumerate(state):
        bits = list(f"{index:0{size}b}")
        a, b = int(bits[first]), int(bits[second])
        if gate == "CX" and a:
            bits[second] = str(1 - b)
        elif gate == "CZ" and a and b:
            amplitude = -amplitude
        elif gate == "SWAP":
            bits[first], bits[second] = bits[second], bits[first]
        output[int("".join(bits), 2)] += amplitude
    return output


def run(program: Program) -> Execution:
    """Execute a parsed E7Q program and collect seeded shot results."""
    state = np.zeros(2**program.qubits, complex)
    state[0] = 1
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
        elif operation.gate in _TWO_QUBIT:
            state = _apply_two(state, operation.gate, *operation.qubits, program.qubits)
        proof.append({
            "step": len(proof),
            "kind": "transform",
            "operator": operation.gate,
            "qubits": list(operation.qubits),
            "state_norm": float(np.vdot(state, state).real),
        })
    raw = np.abs(state) ** 2
    labels = [f"{index:0{program.qubits}b}" for index in range(len(raw))]
    probabilities = {
        label: float(value) for label, value in zip(labels, raw) if value > 1e-15
    }
    rng = np.random.default_rng(program.seed)
    samples = rng.choice(labels, size=program.shots, p=raw)
    counts = {label: int(np.count_nonzero(samples == label)) for label in labels}
    counts = {label: count for label, count in counts.items() if count}
    proof.append({
        "step": len(proof),
        "kind": "project",
        "operator": "measure",
        "shots": program.shots,
        "outcomes": counts,
    })
    return Execution(program, state, probabilities, counts, tuple(proof))


def verify(execution: Execution, tolerance: float = 1e-12) -> dict[str, object]:
    """Evaluate declared invariants and return a machine-readable result."""
    checks: list[dict[str, object]] = []
    if execution.program.require_normalized:
        norm = float(np.vdot(execution.state, execution.state).real)
        checks.append({"name": "normalized", "passed": abs(norm - 1.0) <= tolerance})
    if execution.program.allowed_outcomes is not None:
        observed = {key for key, value in execution.probabilities.items() if value > tolerance}
        checks.append({
            "name": "outcomes",
            "passed": observed <= execution.program.allowed_outcomes,
            "allowed": sorted(execution.program.allowed_outcomes),
            "observed": sorted(observed),
        })
    return {
        "status": "PASS" if all(check["passed"] for check in checks) else "FAIL",
        "checks": checks,
        "probabilities": execution.probabilities,
        "counts": execution.counts,
        "proof": list(execution.proof),
    }


def proof_json(result: dict[str, object]) -> str:
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


def openqasm(program: Program) -> str:
    """Export the v0.1 gate subset to OpenQASM 3."""
    lines = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"qubit[{program.qubits}] q;",
        f"bit[{program.bits}] c;",
    ]
    names = {"CX": "cx", "CZ": "cz", "SWAP": "swap"}
    for operation in program.operations:
        if operation.gate == "MEASURE":
            lines.append("c = measure q;")
        elif len(operation.qubits) == 1:
            lines.append(f"{operation.gate.lower()} q[{operation.qubits[0]}];")
        else:
            a, b = operation.qubits
            lines.append(f"{names[operation.gate]} q[{a}], q[{b}];")
    return "\n".join(lines) + "\n"


def load(path: str | Path) -> Program:
    return parse(Path(path).read_text(encoding="utf-8"))
