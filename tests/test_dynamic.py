# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from e7q.language import E7QError, compare, load, openqasm, run, verify


EXAMPLES = Path(__file__).parents[1] / "examples"


def test_teleportation_uses_measurement_and_feed_forward():
    program = load(EXAMPLES / "teleportation.e7q")
    result = verify(run(program))
    assert result["status"] == "PASS"
    assert sum(result["counts"].values()) == 4096
    assert set(result["counts"]) <= {"001", "011", "101", "111"}
    kinds = [step["kind"] for step in result["proof"]]
    assert kinds.count("project") == 3
    assert kinds.count("conditional-transform") == 2
    condition_steps = [
        step for step in result["proof"] if step["kind"] == "conditional-transform"
    ]
    assert all(step["executed"] + step["skipped"] == 4096 for step in condition_steps)


def test_deutsch_jozsa_balanced_oracle_is_detected():
    result = verify(run(load(EXAMPLES / "deutsch-jozsa-balanced.e7q")))
    assert result["status"] == "PASS"
    assert set(result["probabilities"]) <= {"10", "11"}


def test_dynamic_openqasm_export():
    qasm = openqasm(load(EXAMPLES / "teleportation.e7q"))
    assert "c[0] = measure q[0];" in qasm
    assert "if (c[1] == 1) x q[2];" in qasm


def test_unitary_comparison_rejects_dynamic_programs():
    dynamic = load(EXAMPLES / "teleportation.e7q")
    with pytest.raises(E7QError, match="mid-circuit"):
        compare(dynamic, dynamic)
