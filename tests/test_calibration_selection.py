# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

import pytest

from e7q.calibration import load_snapshot, select_target
from e7q.cli import main
from e7q.language import E7QError, load


ROOT = Path(__file__).parents[1]
PROGRAM = ROOT / "examples" / "nonlocal-cx.e7q"
SNAPSHOT = ROOT / "examples" / "calibration-snapshot.json"


def test_selects_best_compatible_snapshot_target():
    result = select_target(load(PROGRAM), load_snapshot(SNAPSHOT))
    assert result["status"] == "PASS"
    assert result["selected"] == "reference-all-to-all-3"
    assert result["ranking"][0]["estimated"]["success_proxy"] == result["score"]
    assert result["proof"][-1]["kind"] == "target-selection"


def test_rejects_unavailable_and_incompatible_targets(tmp_path):
    snapshot = json.loads(SNAPSHOT.read_text())
    snapshot["targets"][0]["available"] = False
    snapshot["targets"][1]["qubits"] = 2
    path = tmp_path / "none.json"
    path.write_text(json.dumps(snapshot))
    with pytest.raises(E7QError, match="no compatible targets"):
        select_target(load(PROGRAM), load_snapshot(path))


def test_snapshot_schema_and_error_rates_are_validated(tmp_path):
    snapshot = json.loads(SNAPSHOT.read_text())
    snapshot["targets"][0]["single_qubit_error"] = 1.1
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(snapshot))
    result = select_target(load(PROGRAM), load_snapshot(path))
    assert result["selected"] == "reference-all-to-all-3"
    assert "between zero and one" in result["rejected"][0]["reason"]


def test_select_cli_writes_proof(tmp_path):
    proof = tmp_path / "selection.proof.json"
    assert main([
        "select", str(PROGRAM), "--snapshot", str(SNAPSHOT), "--proof", str(proof)
    ]) == 0
    content = proof.read_text()
    assert '"selected": "reference-all-to-all-3"' in content
    assert '"calibration-snapshot"' in content
