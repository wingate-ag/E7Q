# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from e7q.cli import main
from e7q.language import E7QError
from e7q.observations import conformance_checks
from e7q.results import build_execution_receipt


def bundle():
    return {
        "schema": "e7q.execution-bundle/v1",
        "status": "READY",
        "submitted": False,
        "target": "test-target",
        "shots": 100,
        "source_digest": "sha256:source",
        "openqasm_digest": "sha256:qasm",
    }


def result():
    return {
        "schema": "e7q.execution-result/v1",
        "provider": "example-provider",
        "job_id": "job-123",
        "target": "test-target",
        "shots": 100,
        "counts": {"00": 48, "11": 52},
        "completed_at": "2026-07-29T12:00:00Z",
    }


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def test_receipt_validates_linkage_and_probabilities():
    receipt = build_execution_receipt(bundle(), encode(bundle()), result(), encode(result()))
    assert receipt["schema"] == "e7q.execution-receipt/v1"
    assert "observational_claim_pilot" not in receipt
    assert receipt["status"] == "PASS"
    assert receipt["probabilities"] == {"00": 0.48, "11": 0.52}
    assert receipt["proof"][-1]["kind"] == "evidence-boundary"
    assert receipt["temporal_evidence"]["temporal_order_roles"] == ["TD0"]
    assert (
        receipt["temporal_evidence"]["clock"]["status"]
        == "provider-reported-not-authenticated"
    )


def test_rejects_target_and_count_mismatches():
    wrong_target = result()
    wrong_target["target"] = "other"
    with pytest.raises(E7QError, match="target"):
        build_execution_receipt(bundle(), encode(bundle()), wrong_target, encode(wrong_target))
    wrong_counts = result()
    wrong_counts["counts"] = {"00": 99}
    with pytest.raises(E7QError, match="sum"):
        build_execution_receipt(bundle(), encode(bundle()), wrong_counts, encode(wrong_counts))


def test_receipt_observation_pilot_separates_record_claim_and_interpretation():
    receipt = build_execution_receipt(
        bundle(),
        encode(bundle()),
        result(),
        encode(result()),
        include_observational_claim_pilot=True,
    )
    pilot_value = receipt["observational_claim_pilot"]
    assert pilot_value["observation_records"][0]["recorded_content"]["counts"] == {
        "00": 48,
        "11": 52,
    }
    assert pilot_value["observational_claims"][0]["claim_type"] == "observational-claim"
    assert pilot_value["interpretations"][0]["claim_type"] == "interpretation"
    assert all(check["passed"] for check in conformance_checks(pilot_value))


def test_cli_writes_receipt(tmp_path):
    bundle_path = tmp_path / "bundle.json"
    result_path = tmp_path / "result.json"
    output = tmp_path / "receipt.json"
    bundle_path.write_text(json.dumps(bundle()), encoding="utf-8")
    result_path.write_text(json.dumps(result()), encoding="utf-8")
    assert main([
        "receipt", str(bundle_path), "--result", str(result_path),
        "--observation-pilot", "-o", str(output)
    ]) == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "PASS"
    assert receipt["counts"] == {"00": 48, "11": 52}
    assert receipt["observational_claim_pilot"]["invoked"] is True
