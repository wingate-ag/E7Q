# SPDX-License-Identifier: Apache-2.0
from e7q.orientation import conformance_checks, temporal_orientation_pilot


def pilot():
    return temporal_orientation_pilot(
        pilot_id="test-orientation",
        orientation_ref="later receipt to compatible execution histories",
        observer_temporal_locality_ref="offline review after receipt construction",
        directional_relation_kinds=[
            "observationalPrecedence",
            "reconstructivePrecedence",
            "globalConsistency",
        ],
        reverse_representation_ref="reverse traversal of the proof path",
        preserved_under_reversal=["step membership", "artifact identity"],
        reversed_hidden_or_unsupported=["proof-step order", "physical causation"],
        time_reversal_symmetry_status="not-assessed",
        causal_reversal_status="unsupported",
        final_constraint_refs=[],
        global_consistency_refs=["bundle/result digest linkage"],
        history_whole_ref="one supplied bundle/result history",
        clock_or_synchronisation_model_ref="provider-reported completion field",
        accumulated_valid_record_ref="normalized receipt",
        compatible_history_family_ref="temporal_evidence.reconstruction",
        fixed_condition_refs=["bundle bytes", "result bytes", "receipt rules"],
        excluded_history_refs=[],
        exclusion_meaning="incompatibility with the current record, not nonexistence",
        correction_or_retraction_refs=[],
        interaction_rule_refs=[],
        narrowing_status="not-claimed",
        decision_effect="blocks causal overreading of reverse reconstruction",
    )


def test_temporal_orientation_pilot_is_structurally_valid():
    value = pilot()
    assert value["status"] == "informative-pilot"
    assert value["upstream_module"].startswith("E7G-T v0.11-UC4")
    assert all(check["passed"] for check in conformance_checks(value))


def test_unknown_relation_kind_fails():
    value = pilot()
    value["directional_relation_kinds"] = ["retrocausation"]
    failed = {check["name"] for check in conformance_checks(value) if not check["passed"]}
    assert "orientation-pilot:relation-kinds" in failed


def test_corrections_disable_monotonic_narrowing_claim():
    value = pilot()
    value["correction_or_retraction_refs"] = ["corrected result"]
    value["narrowing_status"] = "narrowed-under-fixed-conditions"
    failed = {check["name"] for check in conformance_checks(value) if not check["passed"]}
    assert "orientation-pilot:correction-monotonicity" in failed
