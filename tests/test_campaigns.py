# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from e7q.campaigns import assess_replication
from e7q.cli import main
from e7q.language import E7QError
from e7q.observations import conformance_checks


def receipt(digest, left, right, *, bundle="sha256:bundle", target="backend"):
    return {
        "schema": "e7q.execution-receipt/v1",
        "bundle_digest": bundle,
        "result_digest": digest,
        "target": target,
        "shots": left + right,
        "counts": {"00": left, "11": right},
    }


def test_replication_passes_consistent_runs():
    result = assess_replication([
        receipt("sha256:a", 48, 52),
        receipt("sha256:b", 51, 49),
        receipt("sha256:c", 50, 50),
    ])
    assert result["status"] == "PASS"
    assert result["runs"] == 3
    assert result["total_shots"] == 300
    assert result["maximum_pairwise_tvd"] == pytest.approx(0.03)
    assert result["p_value"] > 0.05
    assert result["temporal_evidence"]["temporal_order_roles"] == ["TD2"]
    assert result["temporal_evidence"]["temporal_phase"]["status"] == "PASS"


def test_replication_fails_inconsistent_run():
    result = assess_replication([
        receipt("sha256:a", 50, 50),
        receipt("sha256:b", 90, 10),
    ])
    assert result["status"] == "FAIL"
    assert result["checks"] == {
        "pairwise_total_variation": False,
        "homogeneity": False,
    }
    assert result["temporal_evidence"]["boundary_crossing"]["detected"] is True


def test_replication_observation_pilot_preserves_divergence_and_unknowns():
    result = assess_replication(
        [
            receipt("sha256:a", 50, 50),
            receipt("sha256:b", 60, 40),
        ],
        include_observational_claim_pilot=True,
    )
    pilot_value = result["observational_claim_pilot"]
    shared = pilot_value["shared_field"]
    assert len(shared["divergences"]) == 1
    assert "causal dependence among runs" in shared["unknowns"]
    assert all(check["passed"] for check in conformance_checks(pilot_value))


def test_replication_rejects_mismatched_or_duplicate_evidence():
    with pytest.raises(E7QError, match="same bundle and target"):
        assess_replication([
            receipt("sha256:a", 50, 50),
            receipt("sha256:b", 50, 50, target="other"),
        ])
    with pytest.raises(E7QError, match="unique result_digest"):
        assess_replication([
            receipt("sha256:a", 50, 50),
            receipt("sha256:a", 50, 50),
        ])


def test_replicate_cli_writes_report(tmp_path):
    paths = []
    for index, value in enumerate([
        receipt("sha256:a", 48, 52),
        receipt("sha256:b", 51, 49),
    ]):
        path = tmp_path / f"receipt-{index}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        paths.append(path)
    output = tmp_path / "replication.json"
    assert main(["replicate", *(str(path) for path in paths), "-o", str(output)]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == "e7q.replication-report/v1"
    assert report["proof"][-1]["kind"] == "evidence-boundary"
