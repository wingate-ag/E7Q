# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from e7q.cli import main
from e7q.language import E7QError
from e7q.trends import assess_trend
from e7q.observations import conformance_checks


def report(bundle, left, right, *, target="backend"):
    return {
        "schema": "e7q.replication-report/v1",
        "bundle_digest": bundle,
        "target": target,
        "total_shots": left + right,
        "pooled_counts": {"00": left, "11": right},
    }


def test_trend_reports_no_breach_for_consistent_series():
    result = assess_trend([
        report("sha256:a", 50, 50),
        report("sha256:b", 49, 51),
        report("sha256:c", 52, 48),
    ])
    assert result["status"] == "NO_TREND_DETECTED"
    assert result["adjusted_significance_level"] == pytest.approx(0.025)
    assert result["first_breach_index"] is None
    assert result["temporal_evidence"]["temporal_order_roles"] == ["TD2"]
    assert result["temporal_evidence"]["boundary_crossing"]["detected"] is False


def test_trend_identifies_first_baseline_relative_breach():
    result = assess_trend([
        report("sha256:a", 50, 50),
        report("sha256:b", 51, 49),
        report("sha256:c", 90, 10),
        report("sha256:d", 95, 5),
    ])
    assert result["status"] == "TREND_DETECTED"
    assert result["first_breach_index"] == 2
    assert result["series"][1]["drift_detected"] is True
    assert result["temporal_evidence"]["boundary_crossing"]["first_index"] == 2


def test_trend_observation_pilot_does_not_invent_temporal_bridge():
    result = assess_trend(
        [
            report("sha256:a", 50, 50),
            report("sha256:b", 51, 49),
            report("sha256:c", 90, 10),
        ],
        include_observational_claim_pilot=True,
    )
    pilot_value = result["observational_claim_pilot"]
    assert pilot_value["temporal_extension_bridges"] == []
    assert "authenticated elapsed time" in pilot_value["shared_field"]["unknowns"]
    assert all(check["passed"] for check in conformance_checks(pilot_value))


def test_trend_requires_three_compatible_campaigns():
    with pytest.raises(E7QError, match="at least two candidate"):
        assess_trend([report("a", 50, 50), report("b", 50, 50)])
    with pytest.raises(E7QError, match="same target"):
        assess_trend([
            report("a", 50, 50),
            report("b", 50, 50),
            report("c", 50, 50, target="other"),
        ])


def test_trend_cli_writes_report(tmp_path):
    paths = []
    for index, counts in enumerate(((50, 50), (49, 51), (52, 48))):
        path = tmp_path / f"campaign-{index}.json"
        path.write_text(json.dumps(report(f"sha256:{index}", *counts)), encoding="utf-8")
        paths.append(path)
    output = tmp_path / "trend.json"
    assert main(["trend", *(str(path) for path in paths), "-o", str(output)]) == 0
    value = json.loads(output.read_text(encoding="utf-8"))
    assert value["schema"] == "e7q.trend-report/v1"
    assert value["proof"][-1]["kind"] == "evidence-boundary"
