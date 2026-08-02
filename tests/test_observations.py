# SPDX-License-Identifier: Apache-2.0
from e7q.observations import (
    conformance_checks,
    interpretation_record,
    observation_record,
    observational_claim,
    observational_claim_pilot,
    shared_observational_field,
)


def pilot():
    record = observation_record(
        observation_id="observation:one",
        observer_ref="instrument:test",
        modelled_entity_ref="entity:test",
        inquiry_profile_ref="inquiry:test",
        semantic_context_ref="context:test",
        viewing_or_measurement_ref="view:test",
        observation_protocol_ref="protocol:test",
        observed_at_or_during="2026-08-02T00:00:00Z",
        temporal_support={"instant": "2026-08-02T00:00:00Z"},
        spatial_or_population_support={"sample": 1},
        resolution="one record",
        recorded_content={"value": 1},
        provenance_refs=["source:test"],
        evidence_refs=["evidence:test"],
        known_limitations=["test limitation"],
        unknown_positions=["unobserved remainder"],
    )
    claim = observational_claim(
        claim_id="claim:one",
        observation_record_refs=["observation:one"],
        asserted_content="The declared instrument recorded value 1.",
        evidence_path=["evidence:test", "claim:one"],
        temporal_support={"instant": "2026-08-02T00:00:00Z"},
        resolution="one record",
        known_limitations=["test limitation"],
        unknown_positions=["unobserved remainder"],
        blocked_overread=["value 1 is a universal or permanent fact"],
    )
    interpretation = interpretation_record(
        interpretation_id="interpretation:one",
        supporting_observation_claim_refs=["claim:one"],
        assumption_refs=["assumption:test"],
        inference_rule_refs=["rule:test"],
        bridge_refs=[],
        external_model_refs=[],
        criterion_refs=["criterion:test@1"],
        conclusion="PASS under the test criterion.",
        inherited_limitations=["test limitation"],
        added_limitations=["test-only criterion"],
        support_basis="mixed",
        support_status="test",
        admissible_use="test structural conformance",
        non_admissible_use="substantive inference",
        validity_window="this test",
        stop_or_reopen_condition="input changes",
    )
    shared = shared_observational_field(
        participating_observer_refs=["instrument:test"],
        participating_observation_record_refs=["observation:one"],
        jointly_admissible_claim_refs=["claim:one"],
        divergences=[],
        unknowns=["unobserved remainder"],
        semantic_conditions=["common test schema"],
        temporal_conditions=["one declared instant"],
        resolution_conditions=["one record"],
        provenance_conditions=["declared test source"],
        admissibility_conditions=["structurally valid record"],
        independence_conditions=["not established"],
    )
    return observational_claim_pilot(
        pilot_id="test-pilot",
        observation_records=[record],
        observational_claims=[claim],
        interpretations=[interpretation],
        shared_field=shared,
    )


def test_observational_claim_pilot_is_structurally_valid():
    value = pilot()
    assert value["status"] == "informative-pilot"
    assert all(check["passed"] for check in conformance_checks(value))


def test_pilot_rejects_dangling_record_reference():
    value = pilot()
    value["observational_claims"][0]["observation_record_refs"] = ["missing"]
    failed = {
        check["name"]
        for check in conformance_checks(value)
        if not check["passed"]
    }
    assert "observation-pilot:claim-0-record-refs" in failed
