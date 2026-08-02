# SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timezone
import json

import pytest

from e7q.cli import main
from e7q.ingestion import ingest_vendor_export
from e7q.language import E7QError
from e7q.observations import conformance_checks


def export(provider="ibm"):
    return {
        "schema": f"e7q.vendor.{provider}/v1",
        "captured_at": "2026-07-29T06:00:00Z",
        "targets": [{
            "name": "test-backend",
            "qubits": 5,
            "topology": "linear",
            "native_gates": ["x", "h", "cx", "swap"],
            "available": True,
            "queue_depth": 3,
            "single_qubit_error": 0.001,
            "two_qubit_error": 0.01,
            "readout_error": 0.02,
        }],
    }


@pytest.mark.parametrize("provider", ["ibm", "google"])
def test_normalizes_supported_vendor_exports(provider):
    result = ingest_vendor_export(provider, export(provider))
    assert result["schema"] == "e7q.calibration/v1"
    assert result["targets"][0]["native_gates"] == ["X", "H", "CX", "SWAP"]
    assert result["targets"][0]["provenance"]["provider"] == provider
    assert result["provenance"]["network_access"] is False
    assert result["temporal_evidence"]["temporal_order_roles"] == ["TD0"]
    assert (
        result["temporal_evidence"]["chronology_status"]
        == "format-validated-not-authenticated"
    )


def test_rejects_wrong_schema_and_stale_exports():
    with pytest.raises(E7QError, match="must use"):
        ingest_vendor_export("google", export("ibm"))
    with pytest.raises(E7QError, match="stale"):
        ingest_vendor_export(
            "ibm",
            export(),
            max_age_hours=1,
            now=datetime(2026, 7, 29, 9, tzinfo=timezone.utc),
        )


def test_records_evaluated_freshness_window():
    result = ingest_vendor_export(
        "ibm",
        export(),
        max_age_hours=4,
        now=datetime(2026, 7, 29, 9, tzinfo=timezone.utc),
    )
    window = result["temporal_evidence"]["validity_window"]
    assert window["status"] == "within-window"
    assert window["age_hours"] == 3


def test_calibration_observation_pilot_is_opt_in_and_bounded():
    result = ingest_vendor_export(
        "ibm",
        export(),
        max_age_hours=4,
        now=datetime(2026, 7, 29, 9, tzinfo=timezone.utc),
        include_observational_claim_pilot=True,
    )
    pilot_value = result["observational_claim_pilot"]
    assert pilot_value["observational_claims"][0]["blocked_overread"]
    assert pilot_value["interpretations"][0]["conclusion"].startswith("within-window")
    assert all(check["passed"] for check in conformance_checks(pilot_value))


def test_cli_writes_normalized_snapshot(tmp_path):
    source = tmp_path / "vendor.json"
    output = tmp_path / "snapshot.json"
    source.write_text(json.dumps(export()), encoding="utf-8")
    assert main([
        "ingest-calibration", str(source), "--provider", "ibm",
        "-o", str(output),
    ]) == 0
    result = json.loads(output.read_text())
    assert result["schema"] == "e7q.calibration/v1"
    assert result["provenance"]["provider"] == "ibm"
