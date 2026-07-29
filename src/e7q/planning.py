# SPDX-License-Identifier: Apache-2.0
"""Backend-neutral resource estimation and target planning."""
from __future__ import annotations

from dataclasses import dataclass

from .language import (
    Compilation, E7QError, Operation, Program, compilation_result,
    compile_topology, topology_edges,
)


@dataclass(frozen=True)
class Resources:
    operations: int
    gate_counts: dict[str, int]
    depth: int
    two_qubit_gates: int
    two_qubit_depth: int


@dataclass(frozen=True)
class Plan:
    source: Resources
    compiled: Resources
    compilation: Compilation
    proof: tuple[dict[str, object], ...]


def _scheduled(
    operations: tuple[Operation, ...], qubits: int
) -> list[tuple[Operation, int]]:
    """Assign each quantum operation to its earliest dependency-safe layer."""
    availability: dict[int, int] = {}
    scheduled: list[tuple[Operation, int]] = []
    barrier = 0
    for operation in operations:
        if operation.gate in {"ASSERT", "NOISE", "MEASURE"}:
            if operation.gate == "MEASURE":
                touched = (
                    tuple(range(qubits))
                    if operation.full_register else operation.qubits
                )
                layer = max(
                    (availability.get(index, barrier) for index in touched),
                    default=barrier,
                ) + 1
                for index in touched:
                    availability[index] = layer
                barrier = layer
                scheduled.append((operation, layer))
            continue
        layer = max(
            (availability.get(index, barrier) for index in operation.qubits),
            default=barrier,
        ) + 1
        for index in operation.qubits:
            availability[index] = layer
        scheduled.append((operation, layer))
    return scheduled


def resources(program: Program) -> Resources:
    """Return deterministic logical resource metrics for a program."""
    scheduled = _scheduled(program.operations, program.qubits)
    counts: dict[str, int] = {}
    for operation, _ in scheduled:
        counts[operation.gate] = counts.get(operation.gate, 0) + 1
    two = [(operation, layer) for operation, layer in scheduled
           if len(operation.qubits) == 2]
    return Resources(
        operations=len(scheduled),
        gate_counts=dict(sorted(counts.items())),
        depth=max((layer for _, layer in scheduled), default=0),
        two_qubit_gates=len(two),
        two_qubit_depth=len({layer for _, layer in two}),
    )


def plan(
    program: Program,
    topology: str = "linear",
    native_gates: frozenset[str] | None = None,
) -> Plan:
    """Compile and compare logical and routed resource requirements."""
    if program.backend != "statevector":
        raise E7QError("target planning currently requires the statevector backend")
    edges = topology_edges(program.qubits, topology)
    compilation = compile_topology(
        program, edges, native_gates
        if native_gates is not None else frozenset(
            {"X", "Y", "Z", "H", "S", "T", "CX", "CZ", "SWAP"}
        ),
    )
    source = resources(program)
    compiled = resources(compilation.program)
    proof = (
        {
            "step": 0,
            "kind": "resource-estimate",
            "stage": "logical",
            **resource_result(source),
        },
        *compilation.proof,
        {
            "step": len(compilation.proof) + 1,
            "kind": "resource-estimate",
            "stage": "compiled",
            **resource_result(compiled),
        },
        {
            "step": len(compilation.proof) + 2,
            "kind": "planning-boundary",
            "statement": (
                "Static estimates only; no queue time, calibration, execution, "
                "cost, or physical fidelity is claimed."
            ),
        },
    )
    return Plan(source, compiled, compilation, tuple(proof))


def resource_result(value: Resources) -> dict[str, object]:
    return {
        "operations": value.operations,
        "gate_counts": value.gate_counts,
        "depth": value.depth,
        "two_qubit_gates": value.two_qubit_gates,
        "two_qubit_depth": value.two_qubit_depth,
    }


def plan_result(value: Plan) -> dict[str, object]:
    compiled = compilation_result(value.compilation)
    return {
        "status": "PASS",
        "source": resource_result(value.source),
        "compiled": resource_result(value.compiled),
        "overhead": {
            "operations": value.compiled.operations - value.source.operations,
            "depth": value.compiled.depth - value.source.depth,
            "two_qubit_gates": (
                value.compiled.two_qubit_gates - value.source.two_qubit_gates
            ),
            "inserted_swaps": value.compilation.inserted_swaps,
        },
        "topology": compiled["topology"],
        "native_gates": compiled["native_gates"],
        "proof": list(value.proof),
    }
