# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from e7q.cli import main
from e7q.language import load
from e7q.planning import plan, plan_result, resources


ROOT = Path(__file__).parents[1]
NONLOCAL = ROOT / "examples" / "nonlocal-cx.e7q"


def test_resources_are_dependency_layered():
    logical = resources(load(NONLOCAL))
    assert logical.gate_counts == {"CX": 1, "H": 1, "MEASURE": 1}
    assert logical.depth == 3
    assert logical.two_qubit_gates == 1
    assert logical.two_qubit_depth == 1


def test_plan_records_routing_overhead_and_boundary():
    result = plan_result(plan(load(NONLOCAL), "linear"))
    assert result["status"] == "PASS"
    assert result["overhead"]["inserted_swaps"] == 2
    assert result["overhead"]["two_qubit_gates"] == 2
    assert result["compiled"]["gate_counts"]["SWAP"] == 2
    assert result["proof"][-1]["kind"] == "planning-boundary"


def test_all_to_all_has_no_routing_overhead():
    result = plan_result(plan(load(NONLOCAL), "all-to-all"))
    assert result["overhead"]["inserted_swaps"] == 0
    assert result["overhead"]["operations"] == 0


def test_plan_cli_writes_machine_readable_proof(tmp_path):
    proof = tmp_path / "plan.proof.json"
    assert main([
        "plan", str(NONLOCAL), "--topology", "linear", "--proof", str(proof)
    ]) == 0
    content = proof.read_text()
    assert '"inserted_swaps": 2' in content
    assert '"planning-boundary"' in content
