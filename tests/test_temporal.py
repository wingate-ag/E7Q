# SPDX-License-Identifier: Apache-2.0
from e7q.temporal import conformance_checks, temporal_evidence


def test_temporal_evidence_record_is_structurally_valid():
    value = temporal_evidence(
        temporal_order_roles=["TD1"],
        carrier_description="ordered test path",
        order_relation="declared step order",
        chronology_status="proof-order-only",
        projection_from="test history",
        projection_to="test summary",
        preserves=["order"],
        loses=["duration"],
        reconstruction_status="non-unique",
        reconstruction_limit="Several histories can produce the summary.",
        criterion_id="e7q.test-completion",
        criterion_edition="1",
        criterion_parameters={},
        criterion="completion",
        phase="COMPLETE",
        boundary_crossing={"detected": False},
    )
    assert value["schema"] == "e7q.temporal-evidence/v2"
    assert value["temporal_order_roles"] == ["TD1"]
    assert all(check["passed"] for check in conformance_checks(value))


def test_temporal_evidence_rejects_unsupported_order_role_and_chronology():
    value = temporal_evidence(
        carrier="T9",
        carrier_description="invalid",
        order_relation="invalid",
        chronology_status="assumed",
        projection_from="source",
        projection_to="view",
        preserves=[],
        loses=[],
        reconstruction_status="not-attempted",
        reconstruction_limit="No reconstruction was attempted.",
    )
    failed = {
        check["name"]
        for check in conformance_checks(value)
        if not check["passed"]
    }
    assert "temporal-evidence:order-roles" in failed
    assert "temporal-evidence:chronology-status" in failed


def test_authenticated_chronology_requires_evidence_reference():
    value = temporal_evidence(
        temporal_order_roles=["TD0"],
        carrier_description="authenticated event",
        order_relation="single event",
        chronology_status="authenticated",
        projection_from="event",
        projection_to="record",
        preserves=["identity"],
        loses=[],
        reconstruction_status="unique-under-declared-model",
        reconstruction_limit="Unique only under the declared event model.",
    )
    failed = {
        check["name"]
        for check in conformance_checks(value)
        if not check["passed"]
    }
    assert "temporal-evidence:chronology-authentication" in failed


def test_legacy_v1_temporal_evidence_remains_readable():
    value = {
        "schema": "e7q.temporal-evidence/v1",
        "carrier": "TD0",
        "carrier_description": "legacy event",
        "order_relation": "single event",
        "chronology_status": "not-established",
        "projection": {
            "from": "source",
            "to": "view",
            "preserves": [],
            "loses": [],
        },
        "reconstruction": {
            "status": "not-attempted",
            "limit": "No reconstruction was attempted.",
        },
    }
    assert all(check["passed"] for check in conformance_checks(value))
