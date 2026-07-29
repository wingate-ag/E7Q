# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from e7q.bundles import build_execution_bundle
from e7q.cli import main
from e7q.language import E7QError, parse


SOURCE = b"""program bundle_demo
qubits 2
bits 2
H 0
CX 0 1
MEASURE
"""


def snapshot():
    return {
        "schema": "e7q.calibration/v1",
        "captured_at": "2026-07-29T06:00:00Z",
        "targets": [{
            "name": "test-target",
            "qubits": 3,
            "topology": "linear",
            "native_gates": ["H", "CX", "SWAP", "MEASURE"],
            "available": True,
            "queue_depth": 1,
            "single_qubit_error": 0.001,
            "two_qubit_error": 0.01,
            "readout_error": 0.02,
        }],
    }


def test_bundle_is_reproducible_and_offline():
    first = build_execution_bundle(parse(SOURCE.decode()), SOURCE, snapshot(), shots=256)
    second = build_execution_bundle(parse(SOURCE.decode()), SOURCE, snapshot(), shots=256)
    assert first == second
    assert first["schema"] == "e7q.execution-bundle/v1"
    assert first["target"] == "test-target"
    assert first["shots"] == 256
    assert first["submitted"] is False
    assert first["source_digest"].startswith("sha256:")
    assert first["openqasm_digest"].startswith("sha256:")
    assert first["proof"][-1]["kind"] == "handoff-boundary"


def test_rejects_invalid_shot_count():
    with pytest.raises(E7QError, match="shots"):
        build_execution_bundle(parse(SOURCE.decode()), SOURCE, snapshot(), shots=0)


def test_cli_writes_bundle(tmp_path):
    source = tmp_path / "program.e7q"
    calibration = tmp_path / "snapshot.json"
    output = tmp_path / "bundle.json"
    source.write_bytes(SOURCE)
    calibration.write_text(json.dumps(snapshot()), encoding="utf-8")
    assert main([
        "bundle", str(source), "--snapshot", str(calibration),
        "--shots", "128", "-o", str(output),
    ]) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "READY"
    assert result["submitted"] is False
    assert result["shots"] == 128
