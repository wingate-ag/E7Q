# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from e7q.cli import main
from e7q.drift import assess_drift
from e7q.language import E7QError
from e7q.observations import conformance_checks


def report(bundle, left, right, *, target="backend"):
    return {
        "schema": "e7q.replication-report/v1",
        "bundle_digest": bundle,
        "target": target,
        "total_shots": left + right,
        "pooled_counts": {"00": left, "11": right},
    }


def test_drift_reports_no_shift_for_consistent_campaigns():
    result = assess_drift(report("sha256:a", 49, 51), report("sha256:b", 51, 49))
    assert result["status"] == "NO_DRIFT"
    assert result["drift_detected"] is False
    assert result["total_variation"] == pytest.approx(0.02)
    assert result["p_value"] > 0.05
    assert result["temporal_evidence"]["temporal_order_roles"] == ["TD2"]
    assert result["temporal_evidence"]["boundary_crossing"]["detected"] is False


def test_drift_detects_distribution_shift():
    result = assess_drift(report("sha256:a", 50, 50), report("sha256:b", 90, 10))
    assert result["status"] == "DRIFT"
    assert result["checks"] == {"total_variation": False, "homogeneity": False}
    assert result["temporal_evidence"]["boundary_crossing"]["detected"] is True


def test_drift_observation_pilot_is_opt_in_and_valid():
    result = assess_drift(
        report("sha256:a", 50, 50),
        report("sha256:b", 90, 10),
        include_observational_claim_pilot=True,
    )
    pilot_value = result["observational_claim_pilot"]
    assert pilot_value["interpretations"][0]["conclusion"].startswith("DRIFT")
    assert all(check["passed"] for check in conformance_checks(pilot_value))


def test_drift_rejects_incompatible_or_malformed_reports():
    with pytest.raises(E7QError, match="same target"):
        assess_drift(report("sha256:a", 50, 50), report("sha256:b", 50, 50, target="other"))
    broken = report("sha256:b", 50, 50)
    broken["total_shots"] = 99
    with pytest.raises(E7QError, match="sum to total_shots"):
        assess_drift(report("sha256:a", 50, 50), broken)


def test_drift_cli_writes_report(tmp_path):
    baseline, candidate = tmp_path / "baseline.json", tmp_path / "candidate.json"
    output = tmp_path / "drift.json"
    baseline.write_text(json.dumps(report("sha256:a", 48, 52)), encoding="utf-8")
    candidate.write_text(json.dumps(report("sha256:b", 52, 48)), encoding="utf-8")
    assert main(["drift", str(baseline), str(candidate), "-o", str(output)]) == 0
    value = json.loads(output.read_text(encoding="utf-8"))
    assert value["schema"] == "e7q.drift-report/v1"
    assert value["proof"][-1]["kind"] == "evidence-boundary"
