# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from e7q.language import from_openqasm, load, openqasm, parse, run, verify


EXAMPLES = Path(__file__).parents[1] / "examples"


def test_reusable_path_and_passing_assertion():
    program = load(EXAMPLES / "diagnostic-composition.e7q")
    assert program.subpaths == ("PrepareAndMeasure",)
    result = verify(run(program))
    assert result["status"] == "PASS"
    assert result["first_failure"] is None


def test_first_failure_identifies_assertion_step():
    source = (EXAMPLES / "diagnostic-composition.e7q").read_text()
    program = parse(source.replace("assert c[0] == 1", "assert c[0] == 0"))
    result = verify(run(program))
    assert result["status"] == "FAIL"
    assert result["first_failure"]["assertion"] == "assert c[0] == 0"
    assert result["first_failure"]["failed_shots"] == 256


def test_openqasm_round_trip_preserves_behavior():
    original = load(EXAMPLES / "diagnostic-composition.e7q")
    imported = from_openqasm(
        openqasm(original), shots=original.shots, seed=original.seed
    )
    before = verify(run(original))
    after = verify(run(imported))
    assert after["status"] == before["status"]
    assert after["counts"] == before["counts"]
    assert after["first_failure"] == before["first_failure"]
