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
    label: str | None = None
    probability: float | None = None


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
    subpaths: tuple[str, ...] = ()


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


@dataclass(frozen=True)
class Compilation:
    program: Program
    topology: tuple[tuple[int, int], ...]
    native_gates: frozenset[str]
    inserted_swaps: int
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
_NOISE_CHANNELS = {"bit_flip", "phase_flip", "depolarizing"}
_EXECUTABLE_GATES = frozenset(_ONE_QUBIT) | _TWO_QUBIT
_CONTEXT_SETTINGS = frozenset({"shots", "backend", "seed"})


def _strip_comments(source: str) -> str:
    """Strip line comments while preserving markers inside quoted values."""
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(source):
        character = source[index]
        if in_string:
            result.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            result.append(character)
            index += 1
            continue
        if character == "#" or source.startswith("//", index):
            newline = source.find("\n", index)
            if newline == -1:
                break
            result.append("\n")
            index = newline + 1
            continue
        result.append(character)
        index += 1
    return "".join(result)


def _required(pattern: str, source: str, label: str) -> re.Match[str]:
    match = re.search(pattern, source, re.S)
    if not match:
        raise E7QError(f"missing or invalid {label}")
    return match


def _exactly_one(pattern: str, source: str, label: str) -> re.Match[str]:
    matches = list(re.finditer(pattern, source, re.S))
    if not matches:
        raise E7QError(f"missing or invalid {label}")
    if len(matches) != 1:
        raise E7QError(f"duplicate {label}")
    return matches[0]


_TOP_LEVEL_DECLARATION = re.compile(
    r"""
    context\s+\w+\s*\{.*?\}
    |(?:qubits|bits)\s+\w+\[\d+\]
    |invariant\s+normalized\b
    |invariant\s+outcomes\s+in\s*\{[^}]+\}
    |path\s+\w+\s*\{.*?\}
    |verify\s+\w+
    """,
    re.S | re.X,
)


def _validate_complete_source(source: str) -> None:
    """Reject non-comment input outside recognized top-level declarations."""
    cursor = 0
    for match in _TOP_LEVEL_DECLARATION.finditer(source):
        unconsumed = source[cursor:match.start()]
        if unconsumed.strip():
            fragment = unconsumed.strip().splitlines()[0]
            raise E7QError(f"unrecognized top-level input: {fragment}")
        cursor = match.end()
    unconsumed = source[cursor:]
    if unconsumed.strip():
        fragment = unconsumed.strip().splitlines()[0]
        raise E7QError(f"unrecognized top-level input: {fragment}")


def _parse_settings(source: str) -> dict[str, str]:
    """Parse a context body without silently dropping malformed fragments."""
    pattern = re.compile(r'(\w+)\s*:\s*("(?:[^"\\]|\\.)*"|[^\s}]+)')
    settings: dict[str, str] = {}
    cursor = 0
    for match in pattern.finditer(source):
        if source[cursor:match.start()].strip():
            fragment = source[cursor:match.start()].strip().splitlines()[0]
            raise E7QError(f"invalid context setting: {fragment}")
        key = match.group(1)
        if key in settings:
            raise E7QError(f"duplicate context setting: {key}")
        settings[key] = match.group(2)
        cursor = match.end()
    if source[cursor:].strip():
        fragment = source[cursor:].strip().splitlines()[0]
        raise E7QError(f"invalid context setting: {fragment}")
    return settings


def parse(source: str) -> Program:
    """Parse E7Q source, including partial measurement and classical control."""
    text = _strip_comments(source)
    _validate_complete_source(text)
    context = _exactly_one(r"context\s+(\w+)\s*\{(.*?)\}", text, "context declaration")
    settings = _parse_settings(context.group(2))
    unknown_settings = sorted(set(settings) - _CONTEXT_SETTINGS)
    if unknown_settings:
        raise E7QError(f"unknown context setting: {unknown_settings[0]}")
    try:
        shots = int(settings.get("shots", "1024"))
    except ValueError as exc:
        raise E7QError("shots must be an integer") from exc
    if shots < 1:
        raise E7QError("shots must be positive")
    backend = settings.get("backend", "statevector")
    if backend not in {"statevector", "densitymatrix"}:
        raise E7QError("backend must be statevector or densitymatrix")
    try:
        seed = int(settings["seed"]) if "seed" in settings else None
    except ValueError as exc:
        raise E7QError("seed must be an integer") from exc
    if seed is not None and seed < 0:
        raise E7QError("seed must be non-negative")

    qreg = _exactly_one(
        r"(?m)^\s*qubits\s+(\w+)\[(\d+)\]", text, "qubit register declaration"
    )
    breg = _exactly_one(
        r"(?m)^\s*bits\s+(\w+)\[(\d+)\]", text, "bit register declaration"
    )
    qname, qubits = qreg.group(1), int(qreg.group(2))
    bname, bits = breg.group(1), int(breg.group(2))
    if qubits < 1 or bits < 1:
        raise E7QError("register sizes must be positive")

    verify_match = _exactly_one(r"verify\s+(\w+)", text, "verify declaration")
    path_blocks: dict[str, str] = {}
    for match in re.finditer(r"path\s+(\w+)\s*\{(.*?)\}", text, re.S):
        name = match.group(1)
        if name in path_blocks:
            raise E7QError(f"duplicate path declaration: {name}")
        path_blocks[name] = match.group(2)
    if not path_blocks:
        raise E7QError("missing or invalid path declaration")
    path = verify_match.group(1)
    if path not in path_blocks:
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
    assert_pattern = re.compile(rf"assert\s+{cref}\s*==\s*([01])\Z")
    use_pattern = re.compile(r"use\s+(\w+)\Z")
    noise_pattern = re.compile(
        rf"noise\s+({'|'.join(sorted(_NOISE_CHANNELS))})"
        rf"\s*\(\s*([0-9]*\.?[0-9]+)\s*\)\s+{qref}\Z"
    )

    operations: list[Operation] = []
    used: list[str] = []
    full_measured = False

    def append_body(body: str, stack: tuple[str, ...]) -> None:
        nonlocal full_measured
        for raw_statement in body.splitlines():
            statement = raw_statement.strip()
            if not statement:
                continue
            match = use_pattern.fullmatch(statement)
            if match:
                target = match.group(1)
                if target not in path_blocks:
                    raise E7QError(f"unknown reusable path: {target}")
                if target in stack:
                    raise E7QError(f"recursive reusable path: {target}")
                used.append(target)
                append_body(path_blocks[target], stack + (target,))
                continue
            if full_measured:
                raise E7QError("full-register measurement must be the final operation")
            match = assert_pattern.fullmatch(statement)
            if match:
                bindex, value = map(int, match.groups())
                if bindex >= bits:
                    raise E7QError("assertion bit index out of range")
                operations.append(
                    Operation("ASSERT", bits=(bindex,), condition=(bindex, value),
                              label=statement)
                )
                continue
            match = noise_pattern.fullmatch(statement)
            if match:
                channel, probability, qindex = match.groups()
                probability, qindex = float(probability), int(qindex)
                if not 0.0 <= probability <= 1.0:
                    raise E7QError("noise probability must be between zero and one")
                if qindex >= qubits:
                    raise E7QError("noise qubit index out of range")
                operations.append(
                    Operation("NOISE", (qindex,), label=channel,
                              probability=probability)
                )
                continue
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
    append_body(path_blocks[path], (path,))
    if not any(operation.gate == "MEASURE" for operation in operations):
        raise E7QError("path must contain measurement")
    if any(operation.gate == "NOISE" for operation in operations):
        if backend != "densitymatrix":
            raise E7QError("noise channels require the densitymatrix backend")
        if any(
            operation.condition is not None
            or (operation.gate == "MEASURE" and not operation.full_register)
            or operation.gate == "ASSERT"
            for operation in operations
        ):
            raise E7QError(
                "densitymatrix noise currently requires terminal full-register measurement"
            )

    normalized = list(re.finditer(r"invariant\s+normalized\b", text))
    if len(normalized) > 1:
        raise E7QError("duplicate normalized invariant")
    require_normalized = bool(normalized)
    outcome_invariants = list(
        re.finditer(r"invariant\s+outcomes\s+in\s*\{([^}]+)\}", text)
    )
    if len(outcome_invariants) > 1:
        raise E7QError("duplicate outcomes invariant")
    outcomes = outcome_invariants[0] if outcome_invariants else None
    allowed = None
    if outcomes:
        allowed = frozenset(item.strip() for item in outcomes.group(1).split(","))
        if any(len(item) != bits or set(item) - {"0", "1"} for item in allowed):
            raise E7QError("outcome invariants must be classical-register-width bit strings")
    return Program(
        context.group(1), shots, backend, seed, qubits, bits, path,
        tuple(operations), allowed, require_normalized, tuple(used),
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
    if program.backend == "densitymatrix":
        return _run_densitymatrix(program)
    if not _is_dynamic(program):
        return _run_unitary(program)

    rng = np.random.default_rng(program.seed)
    counts: dict[str, int] = {}
    stats = [
        {"executed": 0, "skipped": 0, "failed": 0,
         "outcomes": {"0": 0, "1": 0}}
        for _ in program.operations
    ]
    final_state = _initial_state(program)
    for _ in range(program.shots):
        state = _initial_state(program)
        classical = [0] * program.bits
        for index, operation in enumerate(program.operations):
            if operation.gate == "ASSERT":
                stats[index]["executed"] += 1
                bit, value = operation.condition
                if classical[bit] != value:
                    stats[index]["failed"] += 1
                continue
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
        if operation.gate == "ASSERT":
            item = {
                "step": len(proof), "kind": "assert",
                "assertion": operation.label, "executed": stat["executed"],
                "failed": stat["failed"], "passed": stat["failed"] == 0,
            }
        elif operation.gate == "MEASURE":
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


def _operator_matrix(operation: Operation, size: int) -> np.ndarray:
    """Construct a full-system unitary for the small reference backend."""
    dimension = 2**size
    columns: list[np.ndarray] = []
    for basis in range(dimension):
        state = np.zeros(dimension, complex)
        state[basis] = 1
        if operation.gate in _ONE_QUBIT:
            state = _apply_one(
                state, _ONE_QUBIT[operation.gate], operation.qubits[0], size
            )
        else:
            state = _apply_two(state, operation.gate, *operation.qubits, size)
        columns.append(state)
    return np.column_stack(columns)


def _noise_kraus(operation: Operation) -> tuple[np.ndarray, ...]:
    probability = float(operation.probability)
    identity = np.eye(2, dtype=complex)
    if operation.label == "bit_flip":
        return (
            math.sqrt(1 - probability) * identity,
            math.sqrt(probability) * _ONE_QUBIT["X"],
        )
    if operation.label == "phase_flip":
        return (
            math.sqrt(1 - probability) * identity,
            math.sqrt(probability) * _ONE_QUBIT["Z"],
        )
    # Standard single-qubit depolarizing channel:
    # (1-p)ρ + p/3 (XρX + YρY + ZρZ).
    return (
        math.sqrt(1 - probability) * identity,
        math.sqrt(probability / 3) * _ONE_QUBIT["X"],
        math.sqrt(probability / 3) * _ONE_QUBIT["Y"],
        math.sqrt(probability / 3) * _ONE_QUBIT["Z"],
    )


def _embed_one(operator: np.ndarray, target: int, size: int) -> np.ndarray:
    operation = Operation("_embedded", (target,))
    dimension = 2**size
    columns = []
    for basis in range(dimension):
        state = np.zeros(dimension, complex)
        state[basis] = 1
        columns.append(_apply_one(state, operator, target, size))
    return np.column_stack(columns)


def _run_densitymatrix(program: Program) -> Execution:
    """Execute unitary evolution plus declared channels as a density matrix."""
    ket = _initial_state(program)
    density = np.outer(ket, ket.conj())
    proof: list[dict[str, object]] = [{
        "step": 0, "kind": "initialize", "backend": "densitymatrix",
        "trace": 1.0, "purity": 1.0,
    }]
    for operation in program.operations:
        if operation.gate == "MEASURE":
            continue
        if operation.gate == "NOISE":
            updated = np.zeros_like(density)
            for local in _noise_kraus(operation):
                kraus = _embed_one(local, operation.qubits[0], program.qubits)
                updated += kraus @ density @ kraus.conj().T
            density = updated
            kind, operator = "channel", operation.label
        else:
            unitary = _operator_matrix(operation, program.qubits)
            density = unitary @ density @ unitary.conj().T
            kind, operator = "transform", operation.gate
        proof.append({
            "step": len(proof), "kind": kind, "operator": operator,
            "qubits": list(operation.qubits),
            "probability": operation.probability,
            "trace": float(np.trace(density).real),
            "purity": float(np.trace(density @ density).real),
        })
    raw = np.real(np.diag(density))
    raw = np.clip(raw, 0.0, 1.0)
    raw /= raw.sum()
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
    return Execution(program, density, probabilities, counts, tuple(proof))


def _run_unitary(program: Program) -> Execution:
    state = _initial_state(program)
    proof: list[dict[str, object]] = [
        {"step": 0, "kind": "initialize", "state_norm": 1.0}
    ]
    for operation in program.operations:
        if operation.gate == "ASSERT":
            raise E7QError("assertions require prior dynamic measurement")
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
    if program.backend != "statevector" or any(
        operation.gate == "NOISE" for operation in program.operations
    ):
        raise E7QError("unitary comparison does not support noise channels")
    dimension = 2**program.qubits
    columns: list[np.ndarray] = []
    for basis in range(dimension):
        state = np.zeros(dimension, complex)
        state[basis] = 1
        for operation in program.operations:
            if operation.gate == "ASSERT":
                raise E7QError("assertions are not unitary operations")
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


def channel_superoperator(program: Program) -> np.ndarray:
    """Return the linear density-matrix map induced before terminal measurement."""
    if program.backend != "densitymatrix":
        raise E7QError("channel comparison requires the densitymatrix backend")
    if _is_dynamic(program) or any(
        operation.gate == "ASSERT" for operation in program.operations
    ):
        raise E7QError(
            "channel comparison does not support mid-circuit measurement, "
            "classical control, or assertions"
        )
    dimension = 2**program.qubits
    columns: list[np.ndarray] = []
    for row in range(dimension):
        for column in range(dimension):
            density = np.zeros((dimension, dimension), complex)
            density[row, column] = 1
            for operation in program.operations:
                if operation.gate == "MEASURE":
                    continue
                if operation.gate == "NOISE":
                    updated = np.zeros_like(density)
                    for local in _noise_kraus(operation):
                        kraus = _embed_one(
                            local, operation.qubits[0], program.qubits
                        )
                        updated += kraus @ density @ kraus.conj().T
                    density = updated
                else:
                    unitary = _operator_matrix(operation, program.qubits)
                    density = unitary @ density @ unitary.conj().T
            columns.append(density.reshape(-1))
    return np.column_stack(columns)


def compare(
    first: Program, second: Program, criterion: str = "global-phase",
    tolerance: float = 1e-12,
) -> Comparison:
    criteria = {
        "exact", "global-phase", "measurement", "tolerance",
        "channel-exact", "channel-tolerance", "channel-measurement",
    }
    if criterion not in criteria:
        raise E7QError(f"unknown equivalence criterion: {criterion}")
    if tolerance <= 0:
        raise E7QError("comparison tolerance must be positive")
    if first.qubits != second.qubits:
        raise E7QError("circuits must have the same number of qubits")
    is_channel = criterion.startswith("channel-")
    if is_channel:
        left = channel_superoperator(first)
        right = channel_superoperator(second)
    else:
        left, right = circuit_unitary(first), circuit_unitary(second)
    phase: complex | None = None
    if criterion == "channel-measurement":
        dimension = 2**first.qubits
        diagonal_rows = [index * dimension + index for index in range(dimension)]
        error = float(np.max(np.abs(left[diagonal_rows] - right[diagonal_rows])))
    elif criterion == "measurement":
        error = float(np.max(np.abs(np.abs(left) ** 2 - np.abs(right) ** 2)))
    elif criterion == "global-phase":
        overlap = np.vdot(left.reshape(-1), right.reshape(-1))
        if abs(overlap) > tolerance:
            phase = overlap / abs(overlap)
        adjusted = right / phase if phase is not None else right
        error = float(np.max(np.abs(left - adjusted)))
    else:
        error = float(np.max(np.abs(left - right)))
    threshold = tolerance if criterion not in {"exact", "channel-exact"} else 0.0
    equivalent = error <= threshold
    proof = ({
        "step": 0, "kind": "compare", "left": first.name, "right": second.name,
        "criterion": criterion, "qubits": first.qubits,
        "representation": "superoperator" if is_channel else "unitary",
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


def topology_edges(qubits: int, topology: str) -> tuple[tuple[int, int], ...]:
    """Build a named undirected hardware coupling graph.

    ``topology`` is the legacy E7Q API term for a coupling-graph layout.  It
    does not invoke the E7G-T UC4 mathematical topological-overlay pilot.
    """
    if qubits < 1:
        raise E7QError("topology requires at least one qubit")
    if topology == "linear":
        return tuple((index, index + 1) for index in range(qubits - 1))
    if topology == "ring":
        edges = list((index, index + 1) for index in range(qubits - 1))
        if qubits > 2:
            edges.append((qubits - 1, 0))
        return tuple(edges)
    if topology == "all-to-all":
        return tuple(
            (first, second)
            for first in range(qubits)
            for second in range(first + 1, qubits)
        )
    raise E7QError(f"unknown topology: {topology}")


def _shortest_path(
    start: int, goal: int, qubits: int, edges: tuple[tuple[int, int], ...]
) -> tuple[int, ...]:
    adjacency = {index: set() for index in range(qubits)}
    for first, second in edges:
        if first == second or not (0 <= first < qubits and 0 <= second < qubits):
            raise E7QError("coupling edges must join distinct in-range qubits")
        adjacency[first].add(second)
        adjacency[second].add(first)
    queue: list[tuple[int, ...]] = [(start,)]
    visited = {start}
    while queue:
        path = queue.pop(0)
        if path[-1] == goal:
            return path
        for neighbor in sorted(adjacency[path[-1]]):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + (neighbor,))
    raise E7QError(f"no coupling path between qubits {start} and {goal}")


def compile_topology(
    program: Program,
    edges: tuple[tuple[int, int], ...],
    native_gates: frozenset[str] = _EXECUTABLE_GATES,
) -> Compilation:
    """Route two-qubit gates onto an undirected hardware coupling graph.

    The public function name is retained for compatibility; no mathematical
    topology in the E7G-T UC4 sense is asserted by this compiler.
    """
    unknown = native_gates - _EXECUTABLE_GATES
    if unknown:
        raise E7QError(f"unknown native gates: {', '.join(sorted(unknown))}")
    routed: list[Operation] = []
    proof: list[dict[str, object]] = [{
        "step": 0,
        "kind": "compile",
        "backend": "topology-reference",
        "logical_qubits": program.qubits,
        "coupling_edges": [list(edge) for edge in edges],
        "native_gates": sorted(native_gates),
        "boundary": (
            "Compilation trace over an undirected hardware coupling graph only; "
            "no physical execution or fidelity is implied, and no E7G-T UC4 "
            "mathematical topological overlay is invoked."
        ),
    }]
    inserted = 0
    for source_step, operation in enumerate(program.operations, start=1):
        if operation.gate not in _EXECUTABLE_GATES:
            routed.append(operation)
            continue
        if operation.gate not in native_gates:
            raise E7QError(f"backend does not support native gate {operation.gate}")
        if operation.gate not in _TWO_QUBIT:
            routed.append(operation)
            continue
        path = _shortest_path(
            operation.qubits[0], operation.qubits[1], program.qubits, edges
        )
        swaps = tuple(zip(path[:-2], path[1:-1]))
        if swaps and "SWAP" not in native_gates:
            raise E7QError("routing a non-adjacent gate requires native SWAP")
        for pair in swaps:
            routed.append(Operation("SWAP", pair))
        routed.append(Operation(
            operation.gate, (path[-2], path[-1]), operation.bits,
            operation.condition, operation.full_register, operation.label,
            operation.probability,
        ))
        for pair in reversed(swaps):
            routed.append(Operation("SWAP", pair))
        inserted += 2 * len(swaps)
        proof.append({
            "step": len(proof),
            "kind": "route",
            "source_step": source_step,
            "operator": operation.gate,
            "logical_qubits": list(operation.qubits),
            "physical_path": list(path),
            "inserted_swaps": 2 * len(swaps),
            "layout_restored": True,
        })
    compiled = Program(
        program.name, program.shots, program.backend, program.seed,
        program.qubits, program.bits, program.path, tuple(routed),
        program.allowed_outcomes, program.require_normalized, program.subpaths,
    )
    proof.append({
        "step": len(proof),
        "kind": "compilation-result",
        "source_operations": len(program.operations),
        "compiled_operations": len(routed),
        "inserted_swaps": inserted,
        "layout_restored": True,
    })
    return Compilation(compiled, edges, native_gates, inserted, tuple(proof))


def compilation_result(compilation: Compilation) -> dict[str, object]:
    return {
        "status": "PASS",
        "backend": "topology-reference",
        "inserted_swaps": compilation.inserted_swaps,
        "source_operations": int(compilation.proof[-1]["source_operations"]),
        "compiled_operations": int(compilation.proof[-1]["compiled_operations"]),
        "topology": [list(edge) for edge in compilation.topology],
        "native_gates": sorted(compilation.native_gates),
        "proof": list(compilation.proof),
    }


def verify(execution: Execution, tolerance: float = 1e-12) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    if execution.program.require_normalized:
        if execution.program.backend == "densitymatrix":
            norm = float(np.trace(execution.state).real)
            checks.append({
                "name": "trace-preserving",
                "passed": abs(norm - 1.0) <= tolerance,
                "trace": norm,
            })
        else:
            norm = float(np.vdot(execution.state, execution.state).real)
            checks.append({"name": "normalized", "passed": abs(norm - 1.0) <= tolerance})
    if execution.program.allowed_outcomes is not None:
        observed = {key for key, value in execution.probabilities.items() if value > tolerance}
        checks.append({
            "name": "outcomes", "passed": observed <= execution.program.allowed_outcomes,
            "allowed": sorted(execution.program.allowed_outcomes),
            "observed": sorted(observed),
        })
    failed_step = next(
        (step for step in execution.proof
         if step.get("kind") == "assert" and not step.get("passed", True)),
        None,
    )
    for step in execution.proof:
        if step.get("kind") == "assert":
            checks.append({
                "name": str(step["assertion"]),
                "passed": bool(step["passed"]),
                "failed_shots": int(step["failed"]),
                "step": int(step["step"]),
            })
    result = {
        "status": "PASS" if all(check["passed"] for check in checks) else "FAIL",
        "checks": checks, "probabilities": execution.probabilities,
        "counts": execution.counts, "proof": list(execution.proof),
        "first_failure": (
            {"step": failed_step["step"], "assertion": failed_step["assertion"],
             "failed_shots": failed_step["failed"]}
            if failed_step else None
        ),
    }
    if execution.program.backend == "densitymatrix":
        result["evidence"] = {
            "backend": "densitymatrix",
            "trace": float(np.trace(execution.state).real),
            "purity": float(np.trace(execution.state @ execution.state).real),
            "channels": sum(
                operation.gate == "NOISE"
                for operation in execution.program.operations
            ),
        }
    return result


def proof_json(result: dict[str, object]) -> str:
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


def openqasm(program: Program) -> str:
    lines = [
        "OPENQASM 3.0;", 'include "stdgates.inc";',
        f"qubit[{program.qubits}] q;", f"bit[{program.bits}] c;",
    ]
    names = {"CX": "cx", "CZ": "cz", "SWAP": "swap"}
    for operation in program.operations:
        if operation.gate == "NOISE":
            lines.append(
                f"// e7q-noise {operation.label}({operation.probability:g}) "
                f"q[{operation.qubits[0]}]"
            )
            continue
        if operation.gate == "ASSERT":
            bit, value = operation.condition
            lines.append(f"// e7q-assert c[{bit}] == {value}")
            continue
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


def from_openqasm(source: str, *, name: str = "ImportedCircuit",
                  shots: int = 1024, seed: int | None = None) -> Program:
    """Import the OpenQASM 3 subset emitted by :func:`openqasm`."""
    if shots < 1:
        raise E7QError("shots must be positive")
    if seed is not None and seed < 0:
        raise E7QError("seed must be non-negative")
    qmatch = _required(r"qubit\[(\d+)\]\s+q\s*;", source, "OpenQASM qubits")
    bmatch = _required(r"bit\[(\d+)\]\s+c\s*;", source, "OpenQASM bits")
    qubits, bits = int(qmatch.group(1)), int(bmatch.group(1))
    operations: list[Operation] = []
    one = re.compile(r"(x|y|z|h|s|t)\s+q\[(\d+)\]\s*;")
    two = re.compile(r"(cx|cz|swap)\s+q\[(\d+)\]\s*,\s*q\[(\d+)\]\s*;")
    partial = re.compile(r"c\[(\d+)\]\s*=\s*measure\s+q\[(\d+)\]\s*;")
    conditional = re.compile(
        r"if\s*\(c\[(\d+)\]\s*==\s*([01])\)\s*"
        r"(x|y|z|h|s|t)\s+q\[(\d+)\]\s*;"
    )
    assertion = re.compile(r"//\s*e7q-assert\s+c\[(\d+)\]\s*==\s*([01])")
    for raw in source.splitlines():
        line = raw.strip()
        match = assertion.fullmatch(line)
        if match:
            bit, value = map(int, match.groups())
            operations.append(Operation(
                "ASSERT", bits=(bit,), condition=(bit, value),
                label=f"assert c[{bit}] == {value}",
            ))
            continue
        match = conditional.fullmatch(line)
        if match:
            bit, value, gate, target = match.groups()
            operations.append(Operation(
                gate.upper(), (int(target),),
                condition=(int(bit), int(value)),
            ))
            continue
        match = partial.fullmatch(line)
        if match:
            bit, target = map(int, match.groups())
            operations.append(Operation("MEASURE", (target,), (bit,)))
            continue
        if re.fullmatch(r"c\s*=\s*measure\s+q\s*;", line):
            operations.append(Operation("MEASURE", full_register=True))
            continue
        match = two.fullmatch(line) or one.fullmatch(line)
        if match:
            operations.append(Operation(
                match.group(1).upper(),
                tuple(int(value) for value in match.groups()[1:]),
            ))
    if not any(operation.gate == "MEASURE" for operation in operations):
        raise E7QError("OpenQASM program must contain measurement")
    return Program(name, shots, "statevector", seed, qubits, bits, name,
                   tuple(operations), None, True)


def load(path: str | Path) -> Program:
    return parse(Path(path).read_text(encoding="utf-8"))


def backend_profile(program: Program) -> dict[str, object]:
    """Return the declared capabilities required to execute a program."""
    return {
        "backend": program.backend,
        "qubits": program.qubits,
        "shots": program.shots,
        "requires": {
            "density_matrix": program.backend == "densitymatrix",
            "mid_circuit_measurement": any(
                operation.gate == "MEASURE" and not operation.full_register
                for operation in program.operations
            ),
            "classical_control": any(
                operation.condition is not None
                for operation in program.operations
                if operation.gate != "ASSERT"
            ),
            "noise_channels": sorted({
                str(operation.label) for operation in program.operations
                if operation.gate == "NOISE"
            }),
        },
        "boundary": (
            "Reference simulator profile; no physical hardware fidelity is implied."
        ),
    }
