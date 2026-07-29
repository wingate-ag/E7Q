# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from e7q.assessment import assess_receipt
from e7q.cli import main
from e7q.language import E7QError


def receipt(counts=None):
    return {
        "schema": "e7q.execution-receipt/v1",
        "shots": 100,
        "counts": counts or {"00": 48, "11": 52},
        "result_digest": "sha256:result",
    }


def reference():
    return {
        "schema": "e7q.reference-distribution/v1",
        "probabilities": {"00": 0.5, "11": 0.5},
        "max_total_variation": 0.1,
        "significance_level": 0.05,
    }


def test_assessment_passes_near_reference():
    result = assess_receipt(receipt(), reference())
    assert result["status"] == "PASS"
    assert result["total_variation"] == pytest.approx(0.02)
    assert result["p_value"] > 0.05
    assert result["warnings"] == []


def test_assessment_fails_large_deviation():
    result = assess_receipt(receipt({"00": 90, "11": 10}), reference())
    assert result["status"] == "FAIL"
    assert result["checks"] == {"total_variation": False, "chi_square": False}


def test_assessment_rejects_invalid_reference():
    invalid = reference()
    invalid["probabilities"] = {"00": 0.6, "11": 0.5}
    with pytest.raises(E7QError, match="sum to one"):
        assess_receipt(receipt(), invalid)


def test_assess_cli_writes_report(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    reference_path = tmp_path / "reference.json"
    output = tmp_path / "assessment.json"
    receipt_path.write_text(json.dumps(receipt()), encoding="utf-8")
    reference_path.write_text(json.dumps(reference()), encoding="utf-8")
    assert main(["assess", str(receipt_path), "--reference", str(reference_path),
                 "-o", str(output)]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == "e7q.execution-assessment/v1"
    assert report["proof"][-1]["kind"] == "evidence-boundary"
