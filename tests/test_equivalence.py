# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from e7q.cli import main
from e7q.language import E7QError, compare, comparison_result, load, parse


EXAMPLES = Path(__file__).parents[1] / "examples"


def _program(name: str, operations: str):
    return parse(f"""
context {name} {{
  backend: statevector
}}
qubits q[1]
bits c[1]
path Circuit {{
{operations}
  measure q -> c
}}
verify Circuit
""")


def test_cancelled_gate_pair_is_exactly_equivalent_to_identity():
    direct = load(EXAMPLES / "identity-direct.e7q")
    optimized = load(EXAMPLES / "identity-optimized.e7q")
    result = comparison_result(compare(direct, optimized, "exact"))
    assert result["status"] == "PASS"
    assert result["maximum_error"] == 0


def test_global_phase_is_distinct_from_exact_equivalence():
    identity = _program("Identity", "")
    phased_identity = _program("PhasedIdentity", "  X q[0]\n  Z q[0]\n  X q[0]\n  Z q[0]")
    assert not compare(identity, phased_identity, "exact").equivalent
    assert compare(identity, phased_identity, "global-phase").equivalent
    assert compare(identity, phased_identity, "measurement").equivalent


def test_measurement_equivalence_is_weaker_than_unitary_equivalence():
    identity = _program("Identity", "")
    phase_flip = _program("PhaseFlip", "  Z q[0]")
    assert not compare(identity, phase_flip, "global-phase").equivalent
    assert compare(identity, phase_flip, "measurement").equivalent


def test_tolerance_criterion_and_validation():
    identity = _program("Identity", "")
    assert compare(identity, identity, "tolerance", 1e-9).equivalent
    with pytest.raises(E7QError, match="positive"):
        compare(identity, identity, tolerance=0)


def test_compare_cli_writes_proof(tmp_path):
    proof = tmp_path / "equivalence.proof.json"
    code = main([
        "compare",
        str(EXAMPLES / "identity-direct.e7q"),
        str(EXAMPLES / "identity-optimized.e7q"),
        "--criterion", "global-phase",
        "--proof", str(proof),
    ])
    assert code == 0
    assert '"status": "PASS"' in proof.read_text(encoding="utf-8")
