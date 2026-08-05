# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from e7q.cli import main
from e7q.language import (
    E7QError, circuit_unitary, compilation_result, compile_topology, load,
    topology_edges,
)


EXAMPLE = Path(__file__).parents[1] / "examples" / "nonlocal-cx.e7q"


def test_linear_routing_preserves_unitary_and_reports_overhead():
    source = load(EXAMPLE)
    compilation = compile_topology(source, topology_edges(3, "linear"))
    assert compilation.inserted_swaps == 2
    assert len(compilation.program.operations) == len(source.operations) + 2
    assert circuit_unitary(compilation.program) == pytest.approx(circuit_unitary(source))
    result = compilation_result(compilation)
    assert result["status"] == "PASS"
    assert result["topology"] == [[0, 1], [1, 2]]
    assert "hardware coupling graph" in result["proof"][0]["boundary"]
    assert "topological overlay" in result["proof"][0]["boundary"]
    assert result["proof"][1]["physical_path"] == [0, 1, 2]
    assert result["proof"][1]["layout_restored"]


def test_all_to_all_requires_no_routing():
    source = load(EXAMPLE)
    compilation = compile_topology(source, topology_edges(3, "all-to-all"))
    assert compilation.inserted_swaps == 0


def test_disconnected_topology_is_rejected():
    with pytest.raises(E7QError, match="no coupling path"):
        compile_topology(load(EXAMPLE), ((0, 1),))


def test_missing_native_gate_is_rejected():
    native = frozenset({"X", "Y", "Z", "H", "S", "T", "CX", "CZ"})
    with pytest.raises(E7QError, match="requires native SWAP"):
        compile_topology(load(EXAMPLE), topology_edges(3, "linear"), native)


def test_compile_cli_writes_qasm_and_proof(tmp_path):
    output = tmp_path / "compiled.qasm"
    proof = tmp_path / "compiled.proof.json"
    assert main([
        "compile", str(EXAMPLE), "--topology", "linear",
        "--output", str(output), "--proof", str(proof),
    ]) == 0
    assert output.read_text().count("swap ") == 2
    assert '"inserted_swaps": 2' in proof.read_text()
