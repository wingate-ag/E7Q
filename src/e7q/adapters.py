# SPDX-License-Identifier: Apache-2.0
"""Dependency-free source adapters for supported quantum SDKs."""
from __future__ import annotations

from dataclasses import dataclass

from .language import E7QError, Program


@dataclass(frozen=True)
class AdapterOutput:
    target: str
    source: str
    proof: tuple[dict[str, object], ...]


def _validate(program: Program, target: str) -> None:
    for operation in program.operations:
        if operation.gate in {"NOISE", "ASSERT"}:
            raise E7QError(f"{target} adapter does not support {operation.gate.lower()}")
        if operation.condition is not None:
            raise E7QError(f"{target} adapter does not support classical control")
        if operation.gate == "MEASURE" and not operation.full_register:
            raise E7QError(f"{target} adapter requires terminal full-register measurement")


def _proof(program: Program, target: str) -> tuple[dict[str, object], ...]:
    return (
        {
            "step": 0,
            "kind": "adapt",
            "target": target,
            "qubits": program.qubits,
            "bits": program.bits,
            "source_operations": len(program.operations),
            "boundary": (
                "Generated SDK source only; no credentials, submission, "
                "calibration, execution, or fidelity claim is included."
            ),
        },
        {
            "step": 1,
            "kind": "adapter-result",
            "target": target,
            "emitted_operations": len(program.operations),
            "status": "PASS",
        },
    )


def qiskit_source(program: Program) -> AdapterOutput:
    """Render a static E7Q program as executable IBM Qiskit Python source."""
    _validate(program, "qiskit")
    lines = [
        "from qiskit import QuantumCircuit",
        "",
        f"circuit = QuantumCircuit({program.qubits}, {program.bits})",
    ]
    methods = {"CX": "cx", "CZ": "cz", "SWAP": "swap"}
    for operation in program.operations:
        if operation.gate == "MEASURE":
            for index in range(program.qubits):
                lines.append(f"circuit.measure({index}, {index})")
            continue
        method = methods.get(operation.gate, operation.gate.lower())
        args = ", ".join(str(index) for index in operation.qubits)
        lines.append(f"circuit.{method}({args})")
    lines.append("")
    return AdapterOutput("qiskit", "\n".join(lines), _proof(program, "qiskit"))


def cirq_source(program: Program) -> AdapterOutput:
    """Render a static E7Q program as executable Google Cirq Python source."""
    _validate(program, "cirq")
    lines = [
        "import cirq",
        "",
        f"qubits = cirq.LineQubit.range({program.qubits})",
        "circuit = cirq.Circuit()",
    ]
    names = {
        "X": "X", "Y": "Y", "Z": "Z", "H": "H", "S": "S", "T": "T",
        "CX": "CNOT", "CZ": "CZ", "SWAP": "SWAP",
    }
    for operation in program.operations:
        if operation.gate == "MEASURE":
            refs = ", ".join(f"qubits[{index}]" for index in range(program.qubits))
            lines.append(f'circuit.append(cirq.measure({refs}, key="c"))')
            continue
        refs = ", ".join(f"qubits[{index}]" for index in operation.qubits)
        lines.append(f"circuit.append(cirq.{names[operation.gate]}({refs}))")
    lines.append("")
    return AdapterOutput("cirq", "\n".join(lines), _proof(program, "cirq"))


def adapt(program: Program, target: str) -> AdapterOutput:
    if target == "qiskit":
        return qiskit_source(program)
    if target == "cirq":
        return cirq_source(program)
    raise E7QError(f"unknown adapter target: {target}")


def adapter_result(output: AdapterOutput) -> dict[str, object]:
    return {
        "status": "PASS",
        "target": output.target,
        "proof": list(output.proof),
    }
