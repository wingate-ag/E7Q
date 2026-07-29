# SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timezone
import json

import pytest

from e7q.cli import main
from e7q.ingestion import ingest_vendor_export
from e7q.language import E7QError


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
