# SPDX-License-Identifier: Apache-2.0
"""Opt-in E7G-T UC2 observation/interpretation pilot records."""
from __future__ import annotations

from typing import Any


SCHEMA = "e7q.observational-claim-pilot/v1alpha1"
UPSTREAM_MODULE = "E7G-T v0.11-UC2 sections 3.9, 16.6, and 19.7"


def observation_record(
    *,
    observation_id: str,
    observer_ref: str,
    modelled_entity_ref: str,
    inquiry_profile_ref: str,
    semantic_context_ref: str,
    viewing_or_measurement_ref: str,
    observation_protocol_ref: str,
    observed_at_or_during: object,
    temporal_support: object,
    spatial_or_population_support: object,
    resolution: object,
    recorded_content: object,
    provenance_refs: list[str],
    evidence_refs: list[str],
    known_limitations: list[str],
    unknown_positions: list[str],
) -> dict[str, object]:
    """Build one observer-indexed record of declared supplied evidence."""
    return {
        "observation_id": observation_id,
        "observer_ref": observer_ref,
        "modelled_entity_ref": modelled_entity_ref,
        "inquiry_profile_ref": inquiry_profile_ref,
        "semantic_context_ref": semantic_context_ref,
        "viewing_or_measurement_ref": viewing_or_measurement_ref,
        "observation_protocol_ref": observation_protocol_ref,
        "observed_at_or_during": observed_at_or_during,
        "temporal_support": temporal_support,
        "spatial_or_population_support": spatial_or_population_support,
        "resolution": resolution,
        "recorded_content": recorded_content,
        "provenance_refs": provenance_refs,
        "evidence_refs": evidence_refs,
        "known_limitations": known_limitations,
        "unknown_positions": unknown_positions,
    }


def observational_claim(
    *,
    claim_id: str,
    observation_record_refs: list[str],
    asserted_content: object,
    evidence_path: list[str],
    temporal_support: object,
    resolution: object,
    known_limitations: list[str],
    unknown_positions: list[str],
    blocked_overread: list[str],
) -> dict[str, object]:
    """Build a claim bounded to the content licensed by its records."""
    return {
        "claim_id": claim_id,
        "claim_type": "observational-claim",
        "observation_record_refs": observation_record_refs,
        "asserted_content": asserted_content,
        "evidence_path": evidence_path,
        "temporal_support": temporal_support,
        "resolution": resolution,
        "known_limitations": known_limitations,
        "unknown_positions": unknown_positions,
        "blocked_overread": blocked_overread,
    }


def interpretation_record(
    *,
    interpretation_id: str,
    supporting_observation_claim_refs: list[str],
    assumption_refs: list[str],
    inference_rule_refs: list[str],
    bridge_refs: list[str],
    external_model_refs: list[str],
    criterion_refs: list[str],
    conclusion: object,
    inherited_limitations: list[str],
    added_limitations: list[str],
    support_basis: str,
    support_status: str,
    admissible_use: object,
    non_admissible_use: object,
    validity_window: object,
    stop_or_reopen_condition: object,
) -> dict[str, object]:
    """Build an interpretation with its added inferential machinery exposed."""
    return {
        "interpretation_id": interpretation_id,
        "claim_type": "interpretation",
        "supporting_observation_claim_refs": supporting_observation_claim_refs,
        "assumption_refs": assumption_refs,
        "inference_rule_refs": inference_rule_refs,
        "bridge_refs": bridge_refs,
        "external_model_refs": external_model_refs,
        "criterion_refs": criterion_refs,
        "conclusion": conclusion,
        "inherited_limitations": inherited_limitations,
        "added_limitations": added_limitations,
        "support_basis": support_basis,
        "support_status": support_status,
        "admissible_use": admissible_use,
        "non_admissible_use": non_admissible_use,
        "validity_window": validity_window,
        "stop_or_reopen_condition": stop_or_reopen_condition,
    }


def shared_observational_field(
    *,
    participating_observer_refs: list[str],
    participating_observation_record_refs: list[str],
    jointly_admissible_claim_refs: list[str],
    divergences: list[object],
    unknowns: list[object],
    semantic_conditions: list[str],
    temporal_conditions: list[str],
    resolution_conditions: list[str],
    provenance_conditions: list[str],
    admissibility_conditions: list[str],
    independence_conditions: list[str],
) -> dict[str, object]:
    """Represent UC2's shared field as joint content, divergence, and unknowns."""
    return {
        "participating_observer_refs": participating_observer_refs,
        "participating_observation_record_refs": participating_observation_record_refs,
        "jointly_admissible_claim_refs": jointly_admissible_claim_refs,
        "divergences": divergences,
        "unknowns": unknowns,
        "composition_conditions": {
            "semantic": semantic_conditions,
            "temporal": temporal_conditions,
            "resolution": resolution_conditions,
            "provenance": provenance_conditions,
            "admissibility": admissibility_conditions,
            "independence": independence_conditions,
        },
    }


def observational_claim_pilot(
    *,
    pilot_id: str,
    observation_records: list[dict[str, object]],
    observational_claims: list[dict[str, object]],
    interpretations: list[dict[str, object]],
    shared_field: dict[str, object] | None = None,
    temporal_extension_bridges: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build the versioned, explicitly invoked UC2 pilot envelope."""
    return {
        "schema": SCHEMA,
        "upstream_module": UPSTREAM_MODULE,
        "status": "informative-pilot",
        "invoked": True,
        "pilot_id": pilot_id,
        "observation_records": observation_records,
        "observational_claims": observational_claims,
        "interpretations": interpretations,
        "shared_field": shared_field,
        "temporal_extension_bridges": temporal_extension_bridges or [],
    }


def conformance_checks(value: Any) -> list[dict[str, object]]:
    """Return structural and reference-integrity checks for a pilot record."""

    def check(name: str, passed: bool) -> dict[str, object]:
        return {"name": f"observation-pilot:{name}", "passed": passed}

    def nonempty(item: object) -> bool:
        return isinstance(item, str) and bool(item)

    def string_list(item: object, *, allow_empty: bool = True) -> bool:
        return (
            isinstance(item, list)
            and (allow_empty or bool(item))
            and all(nonempty(entry) for entry in item)
        )

    if not isinstance(value, dict):
        return [check("object", False)]

    records = value.get("observation_records")
    claims = value.get("observational_claims")
    interpretations = value.get("interpretations")
    checks = [
        check("schema", value.get("schema") == SCHEMA),
        check("invoked", value.get("invoked") is True),
        check("pilot-id", nonempty(value.get("pilot_id"))),
        check("records", isinstance(records, list) and bool(records)),
        check("claims", isinstance(claims, list) and bool(claims)),
        check("interpretations", isinstance(interpretations, list)),
        check(
            "temporal-extension-bridges",
            isinstance(value.get("temporal_extension_bridges"), list),
        ),
    ]
    if not isinstance(records, list) or not isinstance(claims, list):
        return checks

    record_ids: list[str] = []
    required_record_fields = (
        "observer_ref",
        "modelled_entity_ref",
        "inquiry_profile_ref",
        "semantic_context_ref",
        "viewing_or_measurement_ref",
        "observation_protocol_ref",
    )
    for index, record in enumerate(records):
        valid_record = isinstance(record, dict)
        checks.append(check(f"record-{index}-object", valid_record))
        if not valid_record:
            continue
        record_id = record.get("observation_id")
        checks.append(check(f"record-{index}-id", nonempty(record_id)))
        if isinstance(record_id, str):
            record_ids.append(record_id)
        checks.append(
            check(
                f"record-{index}-context",
                all(nonempty(record.get(field)) for field in required_record_fields),
            )
        )
        checks.append(
            check(
                f"record-{index}-support",
                all(
                    record.get(field) is not None
                    for field in (
                        "temporal_support",
                        "spatial_or_population_support",
                        "resolution",
                        "recorded_content",
                    )
                ),
            )
        )
        for field in (
            "provenance_refs",
            "evidence_refs",
            "known_limitations",
            "unknown_positions",
        ):
            checks.append(
                check(f"record-{index}-{field}", string_list(record.get(field)))
            )
    checks.append(check("record-ids-unique", len(record_ids) == len(set(record_ids))))

    claim_ids: list[str] = []
    for index, claim in enumerate(claims):
        valid_claim = isinstance(claim, dict)
        checks.append(check(f"claim-{index}-object", valid_claim))
        if not valid_claim:
            continue
        claim_id = claim.get("claim_id")
        checks.append(check(f"claim-{index}-id", nonempty(claim_id)))
        if isinstance(claim_id, str):
            claim_ids.append(claim_id)
        refs = claim.get("observation_record_refs")
        checks.append(
            check(
                f"claim-{index}-record-refs",
                string_list(refs, allow_empty=False)
                and set(refs).issubset(set(record_ids)),
            )
        )
        checks.append(
            check(
                f"claim-{index}-boundary",
                claim.get("asserted_content") is not None
                and string_list(claim.get("evidence_path"), allow_empty=False)
                and string_list(claim.get("known_limitations"))
                and string_list(claim.get("unknown_positions"))
                and string_list(claim.get("blocked_overread"), allow_empty=False),
            )
        )
    checks.append(check("claim-ids-unique", len(claim_ids) == len(set(claim_ids))))

    if isinstance(interpretations, list):
        interpretation_ids: list[str] = []
        for index, interpretation in enumerate(interpretations):
            valid = isinstance(interpretation, dict)
            checks.append(check(f"interpretation-{index}-object", valid))
            if not valid:
                continue
            interpretation_id = interpretation.get("interpretation_id")
            checks.append(check(f"interpretation-{index}-id", nonempty(interpretation_id)))
            if isinstance(interpretation_id, str):
                interpretation_ids.append(interpretation_id)
            refs = interpretation.get("supporting_observation_claim_refs")
            checks.append(
                check(
                    f"interpretation-{index}-claim-refs",
                    string_list(refs, allow_empty=False)
                    and set(refs).issubset(set(claim_ids)),
                )
            )
            checks.append(
                check(
                    f"interpretation-{index}-machinery",
                    all(
                        string_list(interpretation.get(field))
                        for field in (
                            "assumption_refs",
                            "inference_rule_refs",
                            "bridge_refs",
                            "external_model_refs",
                            "criterion_refs",
                            "inherited_limitations",
                            "added_limitations",
                        )
                    ),
                )
            )
            checks.append(
                check(
                    f"interpretation-{index}-use-boundary",
                    interpretation.get("conclusion") is not None
                    and nonempty(interpretation.get("support_basis"))
                    and nonempty(interpretation.get("support_status"))
                    and interpretation.get("admissible_use") is not None
                    and interpretation.get("non_admissible_use") is not None
                    and interpretation.get("stop_or_reopen_condition") is not None,
                )
            )
        checks.append(
            check(
                "interpretation-ids-unique",
                len(interpretation_ids) == len(set(interpretation_ids)),
            )
        )

    shared = value.get("shared_field")
    checks.append(check("shared-field", shared is None or isinstance(shared, dict)))
    if isinstance(shared, dict):
        participants = shared.get("participating_observation_record_refs")
        joint = shared.get("jointly_admissible_claim_refs")
        conditions = shared.get("composition_conditions")
        checks.extend(
            [
                check(
                    "shared-observer-refs",
                    string_list(
                        shared.get("participating_observer_refs"), allow_empty=False
                    ),
                ),
                check(
                    "shared-record-refs",
                    string_list(participants, allow_empty=False)
                    and set(participants).issubset(set(record_ids)),
                ),
                check(
                    "shared-claim-refs",
                    string_list(joint)
                    and set(joint).issubset(set(claim_ids)),
                ),
                check("shared-divergences", isinstance(shared.get("divergences"), list)),
                check("shared-unknowns", isinstance(shared.get("unknowns"), list)),
                check("shared-conditions", isinstance(conditions, dict)),
            ]
        )
        if isinstance(conditions, dict):
            checks.append(
                check(
                    "shared-condition-lists",
                    all(
                        string_list(conditions.get(field))
                        for field in (
                            "semantic",
                            "temporal",
                            "resolution",
                            "provenance",
                            "admissibility",
                            "independence",
                        )
                    ),
                )
            )
    return checks
