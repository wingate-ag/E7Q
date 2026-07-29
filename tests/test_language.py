# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import numpy as np
import pytest

from e7q.language import E7QError, load, openqasm, parse, run, verify


BELL = Path(__file__).parents[1] / "examples" / "bell.e7q"


def test_bell_source_parses_executes_and_verifies():
    execution = run(load(BELL))
    assert np.allclose(
        [execution.probabilities.get(f"{i:02b}", 0) for i in range(4)],
        [0.5, 0, 0, 0.5],
    )
    result = verify(execution)
    assert result["status"] == "PASS"
    assert all(check["passed"] for check in result["checks"])
    assert sum(result["counts"].values()) == 1000
    assert set(result["counts"]) <= {"00", "11"}
    assert [item["kind"] for item in result["proof"]] == [
        "initialize", "transform", "transform", "project"
    ]


def test_seed_makes_measurement_reproducible():
    program = load(BELL)
    assert run(program).counts == run(program).counts


def test_openqasm_export():
    qasm = openqasm(load(BELL))
    assert "OPENQASM 3.0;" in qasm
    assert "h q[0];" in qasm
    assert "cx q[0], q[1];" in qasm
    assert "c = measure q;" in qasm


@pytest.mark.parametrize(
    "mutation,message",
    [
        (lambda text: text.replace("q[1]", "q[2]", 1), "out of range"),
        (lambda text: text.replace("measure q -> c", ""), "measurement"),
        (lambda text: text.replace("verify CreateBellPair", "verify Missing"), "verify target"),
    ],
)
def test_invalid_programs_are_rejected(mutation, message):
    with pytest.raises(E7QError, match=message):
        parse(mutation(BELL.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda text: "unknown top-level declaration\n" + text,
        lambda text: text + "\nunknown trailing declaration\n",
        lambda text: text.replace(
            "qubits q[2]", "qubits q[2]\nunknown between declarations", 1
        ),
    ],
)
def test_unconsumed_non_comment_input_is_rejected(mutation):
    with pytest.raises(E7QError, match="unrecognized top-level input"):
        parse(mutation(BELL.read_text(encoding="utf-8")))


def test_unconsumed_context_input_is_rejected():
    source = BELL.read_text(encoding="utf-8").replace(
        "backend: statevector", "backend: statevector\nmalformed setting", 1
    )
    with pytest.raises(E7QError, match="invalid context setting"):
        parse(source)


def test_comments_and_whitespace_remain_permitted():
    source = (
        "// leading comment\n\n"
        + BELL.read_text(encoding="utf-8")
        + "\n# trailing comment\n"
    )
    assert parse(source).name == load(BELL).name


@pytest.mark.parametrize(
    "mutation,message",
    [
        (
            lambda text: text.replace(
                "qubits q[2]", "context Other { shots: 1 }\nqubits q[2]", 1
            ),
            "duplicate context declaration",
        ),
        (
            lambda text: text.replace("qubits q[2]", "qubits other[1]\nqubits q[2]", 1),
            "duplicate qubit register declaration",
        ),
        (
            lambda text: text.replace("bits c[2]", "bits other[1]\nbits c[2]", 1),
            "duplicate bit register declaration",
        ),
        (
            lambda text: text + "\nverify CreateBellPair\n",
            "duplicate verify declaration",
        ),
        (
            lambda text: text.replace(
                "path CreateBellPair {",
                "path CreateBellPair { measure q -> c }\npath CreateBellPair {",
                1,
            ),
            "duplicate path declaration: CreateBellPair",
        ),
        (
            lambda text: text.replace("shots: 1000", "shots: 1000\nshots: 2", 1),
            "duplicate context setting: shots",
        ),
        (
            lambda text: text.replace(
                "invariant normalized",
                "invariant normalized\ninvariant normalized",
                1,
            ),
            "duplicate normalized invariant",
        ),
        (
            lambda text: text.replace(
                "invariant outcomes in {00, 11}",
                "invariant outcomes in {00, 11}\ninvariant outcomes in {00}",
                1,
            ),
            "duplicate outcomes invariant",
        ),
    ],
)
def test_duplicate_declarations_are_rejected(mutation, message):
    with pytest.raises(E7QError, match=message):
        parse(mutation(BELL.read_text(encoding="utf-8")))


def test_distinct_reusable_paths_remain_permitted():
    source = BELL.read_text(encoding="utf-8").replace(
        "path CreateBellPair {",
        "path Prepare { H q[0] }\n\npath CreateBellPair {\n  use Prepare",
        1,
    )
    assert parse(source).subpaths == ("Prepare",)
