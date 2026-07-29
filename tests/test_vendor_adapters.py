# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from e7q.adapters import adapt, adapter_result
from e7q.cli import main
from e7q.language import E7QError, load


ROOT = Path(__file__).parents[1]
BELL = ROOT / "examples" / "bell.e7q"
DYNAMIC = ROOT / "examples" / "teleportation.e7q"
NOISY = ROOT / "examples" / "noisy-bell.e7q"


def test_qiskit_adapter_emits_complete_static_circuit():
    output = adapt(load(BELL), "qiskit")
    assert "QuantumCircuit(2, 2)" in output.source
    assert "circuit.h(0)" in output.source
    assert "circuit.cx(0, 1)" in output.source
    assert output.source.count("circuit.measure") == 2
    assert adapter_result(output)["status"] == "PASS"


def test_cirq_adapter_emits_complete_static_circuit():
    output = adapt(load(BELL), "cirq")
    assert "cirq.LineQubit.range(2)" in output.source
    assert "cirq.H(qubits[0])" in output.source
    assert "cirq.CNOT(qubits[0], qubits[1])" in output.source
    assert 'key="c"' in output.source


@pytest.mark.parametrize("source", [DYNAMIC, NOISY])
def test_unsupported_programs_are_rejected(source):
    with pytest.raises(E7QError, match="does not support|requires terminal"):
        adapt(load(source), "qiskit")


def test_export_cli_writes_adapter_and_proof(tmp_path):
    output = tmp_path / "bell_qiskit.py"
    proof = tmp_path / "adapter.proof.json"
    assert main([
        "export", str(BELL), "--format", "qiskit",
        "--output", str(output), "--proof", str(proof),
    ]) == 0
    assert "QuantumCircuit" in output.read_text()
    assert '"target": "qiskit"' in proof.read_text()
    compile(output.read_text(), str(output), "exec")
