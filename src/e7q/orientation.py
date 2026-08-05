# SPDX-License-Identifier: Apache-2.0
"""Opt-in E7G-T temporal-orientation pilot records, retained in UC4."""
from __future__ import annotations

from typing import Any


SCHEMA = "e7q.temporal-orientation-pilot/v1alpha1"
UPSTREAM_MODULE = "E7G-T v0.11-UC4 sections 5.13.1-5.13.6, 13.8, and 19.8"

RELATION_KINDS = {
    "clockPrecedence",
    "sequence",
    "dependency",
    "observationalPrecedence",
    "reconstructivePrecedence",
    "generativeCausation",
    "finalConstraint",
    "globalConsistency",
}

REVERSAL_STATUSES = {
    "not-assessed",
    "not-established",
    "unsupported",
    "supported-under-declared-model",
}

NARROWING_STATUSES = {
    "not-assessed",
    "not-claimed",
    "narrowed-under-fixed-conditions",
    "changed-non-monotonically",
}


def temporal_orientation_pilot(
    *,
    pilot_id: str,
    orientation_ref: str,
    observer_temporal_locality_ref: str,
    directional_relation_kinds: list[str],
    reverse_representation_ref: str | None,
    preserved_under_reversal: list[str],
    reversed_hidden_or_unsupported: list[str],
    time_reversal_symmetry_status: str,
    causal_reversal_status: str,
    final_constraint_refs: list[str],
    global_consistency_refs: list[str],
    history_whole_ref: str,
    clock_or_synchronisation_model_ref: str,
    accumulated_valid_record_ref: str,
    compatible_history_family_ref: str,
    fixed_condition_refs: list[str],
    excluded_history_refs: list[str],
    exclusion_meaning: str,
    correction_or_retraction_refs: list[str],
    interaction_rule_refs: list[str],
    narrowing_status: str,
    decision_effect: str,
) -> dict[str, object]:
    """Build an explicitly invoked, non-normative orientation pilot envelope."""
    return {
        "schema": SCHEMA,
        "upstream_module": UPSTREAM_MODULE,
        "status": "informative-pilot",
        "invoked": True,
        "pilot_id": pilot_id,
        "orientation_ref": orientation_ref,
        "observer_temporal_locality_ref": observer_temporal_locality_ref,
        "directional_relation_kinds": directional_relation_kinds,
        "reverse_representation_ref": reverse_representation_ref,
        "preserved_under_reversal": preserved_under_reversal,
        "reversed_hidden_or_unsupported": reversed_hidden_or_unsupported,
        "time_reversal_symmetry_status": time_reversal_symmetry_status,
        "causal_reversal_status": causal_reversal_status,
        "final_constraint_refs": final_constraint_refs,
        "global_consistency_refs": global_consistency_refs,
        "history_whole_ref": history_whole_ref,
        "clock_or_synchronisation_model_ref": clock_or_synchronisation_model_ref,
        "accumulated_valid_record_ref": accumulated_valid_record_ref,
        "compatible_history_family_ref": compatible_history_family_ref,
        "fixed_condition_refs": fixed_condition_refs,
        "excluded_history_refs": excluded_history_refs,
        "exclusion_meaning": exclusion_meaning,
        "correction_or_retraction_refs": correction_or_retraction_refs,
        "interaction_rule_refs": interaction_rule_refs,
        "narrowing_status": narrowing_status,
        "decision_effect": decision_effect,
    }


def conformance_checks(value: Any) -> list[dict[str, object]]:
    """Check the orientation pilot structure and its anti-conflation boundaries."""

    def check(name: str, passed: bool) -> dict[str, object]:
        return {"name": f"orientation-pilot:{name}", "passed": passed}

    def nonempty(item: object) -> bool:
        return isinstance(item, str) and bool(item)

    def string_list(item: object) -> bool:
        return isinstance(item, list) and all(nonempty(entry) for entry in item)

    if not isinstance(value, dict):
        return [check("object", False)]

    relation_kinds = value.get("directional_relation_kinds")
    corrections = value.get("correction_or_retraction_refs")
    narrowing = value.get("narrowing_status")
    reverse_ref = value.get("reverse_representation_ref")
    time_reversal = value.get("time_reversal_symmetry_status")
    causal_reversal = value.get("causal_reversal_status")

    checks = [
        check("schema", value.get("schema") == SCHEMA),
        check("invoked", value.get("invoked") is True),
        check("status", value.get("status") == "informative-pilot"),
        check("pilot-id", nonempty(value.get("pilot_id"))),
        check("orientation", nonempty(value.get("orientation_ref"))),
        check("observer-locality", nonempty(value.get("observer_temporal_locality_ref"))),
        check(
            "relation-kinds",
            string_list(relation_kinds)
            and bool(relation_kinds)
            and len(relation_kinds) == len(set(relation_kinds))
            and set(relation_kinds).issubset(RELATION_KINDS),
        ),
        check("reverse-representation", reverse_ref is None or nonempty(reverse_ref)),
        check("time-reversal-status", time_reversal in REVERSAL_STATUSES),
        check("causal-reversal-status", causal_reversal in REVERSAL_STATUSES),
        check("history-whole", nonempty(value.get("history_whole_ref"))),
        check("clock-model", nonempty(value.get("clock_or_synchronisation_model_ref"))),
        check("accumulated-record", nonempty(value.get("accumulated_valid_record_ref"))),
        check("compatible-history-family", nonempty(value.get("compatible_history_family_ref"))),
        check("exclusion-meaning", nonempty(value.get("exclusion_meaning"))),
        check("narrowing-status", narrowing in NARROWING_STATUSES),
        check("decision-effect", nonempty(value.get("decision_effect"))),
    ]
    list_fields = (
        "preserved_under_reversal",
        "reversed_hidden_or_unsupported",
        "final_constraint_refs",
        "global_consistency_refs",
        "fixed_condition_refs",
        "excluded_history_refs",
        "correction_or_retraction_refs",
        "interaction_rule_refs",
    )
    for field in list_fields:
        checks.append(check(field.replace("_", "-"), string_list(value.get(field))))

    checks.extend(
        [
            check(
                "reverse-boundary",
                reverse_ref is None
                or (
                    time_reversal != "supported-under-declared-model"
                    and causal_reversal != "supported-under-declared-model"
                )
                or "generativeCausation" in set(relation_kinds or []),
            ),
            check(
                "fixed-conditions",
                narrowing != "narrowed-under-fixed-conditions"
                or bool(value.get("fixed_condition_refs")),
            ),
            check(
                "correction-monotonicity",
                not corrections or narrowing != "narrowed-under-fixed-conditions",
            ),
        ]
    )
    return checks
