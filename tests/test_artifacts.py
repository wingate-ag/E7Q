# SPDX-License-Identifier: Apache-2.0
import json

from e7q.artifacts import validate_artifact
from e7q.cli import main


def trend():
    return {
        "schema": "e7q.trend-report/v1",
        "status": "NO_TREND_DETECTED",
        "target": "backend",
        "campaigns": 3,
        "series": [],
        "proof": [{"step": 0, "kind": "test"}],
    }


def test_known_artifact_passes():
    result = validate_artifact(trend())
    assert result["status"] == "PASS"
    assert result["conformance"] == "STRUCTURALLY_CONFORMANT"
    assert result["validation_scope"] == "structure-only"
    assert result["artifact_schema"] == "e7q.trend-report/v1"


def test_missing_required_evidence_fails():
    value = trend()
    del value["proof"]
    result = validate_artifact(value)
    assert result["status"] == "FAIL"
    assert result["conformance"] == "NONCONFORMANT"
    assert any(
        check["name"] == "required-field:proof" and not check["passed"]
        for check in result["checks"]
    )


def test_unknown_schema_fails():
    result = validate_artifact({"schema": "example.unknown/v1"})
    assert result["status"] == "FAIL"
    assert result["conformance"] == "NONCONFORMANT"


def test_invalid_embedded_temporal_evidence_fails():
    value = trend()
    value["temporal_evidence"] = {
        "schema": "e7q.temporal-evidence/v1",
        "carrier": "TD99",
    }
    result = validate_artifact(value)
    assert result["status"] == "FAIL"
    assert any(
        check["name"] == "temporal-evidence:carrier" and not check["passed"]
        for check in result["checks"]
    )


def test_validate_artifact_cli(tmp_path):
    source = tmp_path / "trend.json"
    output = tmp_path / "conformance.json"
    source.write_text(json.dumps(trend()), encoding="utf-8")
    assert main(["validate-artifact", str(source), "-o", str(output)]) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema"] == "e7q.conformance-report/v1"
    assert result["status"] == "PASS"
    assert result["conformance"] == "STRUCTURALLY_CONFORMANT"
