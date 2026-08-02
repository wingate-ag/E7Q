# SPDX-License-Identifier: Apache-2.0
"""Offline longitudinal assessment across supplied replication campaigns."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .drift import assess_drift, load_replication_report
from .language import E7QError
from .observations import (
    interpretation_record,
    observation_record,
    observational_claim,
    observational_claim_pilot,
    shared_observational_field,
)
from .orientation import temporal_orientation_pilot
from .temporal import temporal_evidence


def load_trend_reports(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    reports = [load_replication_report(path) for path in paths]
    if len(reports) < 3:
        raise E7QError("trend assessment requires a baseline and at least two candidate campaigns")
    return reports


def assess_trend(
    reports: list[dict[str, Any]],
    *,
    max_total_variation: float = 0.1,
    significance_level: float = 0.05,
    include_observational_claim_pilot: bool = False,
    include_temporal_orientation_pilot: bool = False,
) -> dict[str, object]:
    """Compare each supplied campaign with the first, controlling repeated tests."""
    if len(reports) < 3:
        raise E7QError("trend assessment requires a baseline and at least two candidate campaigns")
    if not isinstance(significance_level, (int, float)) or isinstance(significance_level, bool) or not 0 < significance_level < 1:
        raise E7QError("significance_level must be between zero and one")
    comparisons = len(reports) - 1
    adjusted = float(significance_level) / comparisons
    baseline = reports[0]
    series: list[dict[str, object]] = []
    first_breach: int | None = None
    for index, candidate in enumerate(reports[1:], start=1):
        drift = assess_drift(
            baseline,
            candidate,
            max_total_variation=max_total_variation,
            significance_level=adjusted,
        )
        breached = drift["status"] == "DRIFT"
        if breached and first_breach is None:
            first_breach = index
        series.append({
            "index": index,
            "bundle_digest": candidate.get("bundle_digest"),
            "shots": candidate.get("total_shots"),
            "status": drift["status"],
            "drift_detected": breached,
            "total_variation": drift["total_variation"],
            "chi_square": drift["chi_square"],
            "degrees_of_freedom": drift["degrees_of_freedom"],
            "p_value": drift["p_value"],
            "checks": drift["checks"],
            "warnings": drift["warnings"],
        })
    status = "TREND_DETECTED" if first_breach is not None else "NO_TREND_DETECTED"
    proof = [
        {"step": 0, "kind": "series-linkage", "target": baseline.get("target"), "campaigns": len(reports), "order": "supplied"},
        {"step": 1, "kind": "multiplicity-control", "method": "bonferroni", "family_significance_level": float(significance_level), "adjusted_significance_level": adjusted, "comparisons": comparisons},
        {"step": 2, "kind": "trend-decision", "status": status, "first_breach_index": first_breach},
        {"step": 3, "kind": "evidence-boundary", "boundary": "Offline baseline-relative comparison in user-supplied order only; not chronology authentication, continuous monitoring, causal attribution, provider authentication, device-stability proof, or physical-fidelity evidence."},
    ]
    report: dict[str, object] = {
        "schema": "e7q.trend-report/v1",
        "status": status,
        "trend_detected": first_breach is not None,
        "target": baseline.get("target"),
        "campaigns": len(reports),
        "baseline": {"index": 0, "bundle_digest": baseline.get("bundle_digest"), "shots": baseline.get("total_shots")},
        "series": series,
        "first_breach_index": first_breach,
        "max_total_variation": float(max_total_variation),
        "significance_level": float(significance_level),
        "adjusted_significance_level": adjusted,
        "multiplicity_method": "bonferroni",
        "temporal_evidence": temporal_evidence(
            temporal_order_roles=["TD2"],
            carrier_description="ordered family of supplied campaign histories",
            order_relation="user-supplied sequence with baseline-relative comparisons",
            chronology_status="declared-not-authenticated",
            projection_from="ordered replication-report family",
            projection_to="baseline-relative longitudinal trend report",
            preserves=[
                "supplied order",
                "campaign identity",
                "first declared threshold breach",
            ],
            loses=[
                "authenticated chronology and elapsed time",
                "unobserved intermediate campaigns",
                "causal explanation",
            ],
            reconstruction_status="non-unique",
            reconstruction_limit=(
                "The supplied series does not determine unobserved intervals "
                "or a unique causal history."
            ),
            criterion_id="e7q.trend-threshold",
            criterion_edition="1",
            criterion_parameters={
                "max_total_variation": float(max_total_variation),
                "family_significance_level": float(significance_level),
                "adjusted_significance_level": adjusted,
                "multiplicity_method": "bonferroni",
            },
            criterion=(
                f"baseline-relative TVD <= {float(max_total_variation)} and "
                f"Bonferroni-adjusted p-value >= {adjusted}"
            ),
            phase=status,
            boundary_crossing={
                "detected": first_breach is not None,
                "first_index": first_breach,
            },
        ),
        "proof": proof,
    }
    if include_observational_claim_pilot:
        records: list[dict[str, object]] = []
        claims: list[dict[str, object]] = []
        record_refs: list[str] = []
        claim_refs: list[str] = []
        for index, source in enumerate(reports):
            record_id = f"observation:campaign-report:{index}"
            claim_id = f"claim:campaign-pooled-counts:{index}"
            source_ref = str(source.get("bundle_digest") or f"campaign:{index}")
            observer_ref = f"software-process:e7q:campaign-report:{source_ref}"
            limitations = [
                "the supplied campaign report is a derived artifact",
                "supplied order is not authenticated chronology",
            ]
            unknowns = [
                "unobserved intermediate campaigns",
                "causes of any distributional changes",
            ]
            records.append(
                observation_record(
                    observation_id=record_id,
                    observer_ref=observer_ref,
                    modelled_entity_ref=source_ref,
                    inquiry_profile_ref="e7q.trend-threshold",
                    semantic_context_ref="e7q.replication-report/v1",
                    viewing_or_measurement_ref="supplied pooled campaign counts",
                    observation_protocol_ref="e7q.trend-input/v1",
                    observed_at_or_during={"supplied_index": index},
                    temporal_support={
                        "supplied_index": index,
                        "chronology_status": "declared-not-authenticated",
                    },
                    spatial_or_population_support={
                        "target": baseline.get("target"),
                        "shots": source.get("total_shots"),
                    },
                    resolution="one pooled campaign distribution",
                    recorded_content={
                        "pooled_counts": source.get("pooled_counts"),
                        "total_shots": source.get("total_shots"),
                    },
                    provenance_refs=[source_ref],
                    evidence_refs=[source_ref],
                    known_limitations=limitations,
                    unknown_positions=unknowns,
                )
            )
            claims.append(
                observational_claim(
                    claim_id=claim_id,
                    observation_record_refs=[record_id],
                    asserted_content=(
                        f"The campaign report supplied at index {index} contains "
                        "the recorded pooled counts and shot total."
                    ),
                    evidence_path=[source_ref, "trend input validation"],
                    temporal_support={"supplied_index": index, "authenticated": False},
                    resolution="one pooled campaign distribution",
                    known_limitations=limitations,
                    unknown_positions=unknowns,
                    blocked_overread=[
                        "the supplied position proves an authenticated date or elapsed interval"
                    ],
                )
            )
            record_refs.append(record_id)
            claim_refs.append(claim_id)
        report["observational_claim_pilot"] = observational_claim_pilot(
            pilot_id="e7q.trend-report",
            observation_records=records,
            observational_claims=claims,
            interpretations=[
                interpretation_record(
                    interpretation_id="interpretation:trend-status",
                    supporting_observation_claim_refs=claim_refs,
                    assumption_refs=[
                        "the supplied sequence is the intended baseline-relative order"
                    ],
                    inference_rule_refs=[
                        "baseline-relative chi-square homogeneity comparisons",
                        "Bonferroni multiplicity control",
                    ],
                    bridge_refs=["pooled counts to empirical distributions"],
                    external_model_refs=["multinomial finite-sample model"],
                    criterion_refs=["e7q.trend-threshold@1"],
                    conclusion=f"{status} under the declared longitudinal thresholds.",
                    inherited_limitations=[
                        "campaign chronology and unobserved intervals are not authenticated"
                    ],
                    added_limitations=[
                        "only baseline-relative comparisons in supplied order are evaluated"
                    ],
                    support_basis="mixed",
                    support_status="operationally-validated-offline",
                    admissible_use=(
                        "locate a declared threshold breach in the supplied campaign sequence"
                    ),
                    non_admissible_use=(
                        "continuous monitoring, causal attribution, future stability, "
                        "or provider and device authentication"
                    ),
                    validity_window="the supplied ordered campaign family",
                    stop_or_reopen_condition=(
                        "reopen if order, reports, thresholds, or multiplicity policy changes"
                    ),
                )
            ],
            shared_field=shared_observational_field(
                participating_observer_refs=[
                    str(record["observer_ref"]) for record in records
                ],
                participating_observation_record_refs=record_refs,
                jointly_admissible_claim_refs=claim_refs,
                divergences=series,
                unknowns=[
                    "unobserved campaigns between supplied positions",
                    "causal explanation for threshold breaches",
                    "authenticated elapsed time",
                ],
                semantic_conditions=["common target and outcome width"],
                temporal_conditions=["user-supplied sequence only"],
                resolution_conditions=["pooled campaign distributions"],
                provenance_conditions=["supplied replication-report artifacts"],
                admissibility_conditions=["valid pooled counts and shot totals"],
                independence_conditions=["campaign independence is not established"],
            ),
            temporal_extension_bridges=[],
        )
    if include_temporal_orientation_pilot:
        report["temporal_orientation_pilot"] = temporal_orientation_pilot(
            pilot_id="e7q.trend-report",
            orientation_ref="supplied baseline-to-later campaign sequence",
            observer_temporal_locality_ref="offline review after the supplied series",
            directional_relation_kinds=[
                "sequence",
                "observationalPrecedence",
                "reconstructivePrecedence",
                "dependency",
                "globalConsistency",
            ],
            reverse_representation_ref="reverse traversal of supplied campaign indices",
            preserved_under_reversal=[
                "campaign membership",
                "pooled distributions",
                "baseline-relative comparison results",
            ],
            reversed_hidden_or_unsupported=[
                "supplied sequence roles",
                "authenticated chronology and elapsed time",
                "causal explanation",
            ],
            time_reversal_symmetry_status="not-assessed",
            causal_reversal_status="unsupported",
            final_constraint_refs=["e7q.trend-threshold@1"],
            global_consistency_refs=["common target and outcome width"],
            history_whole_ref="supplied ordered campaign family",
            clock_or_synchronisation_model_ref=(
                "user-supplied index order; no authenticated clock model"
            ),
            accumulated_valid_record_ref="validated ordered campaign-report family",
            compatible_history_family_ref="temporal_evidence.reconstruction",
            fixed_condition_refs=[
                "supplied campaign order",
                "baseline campaign at index zero",
                "e7q.trend-threshold@1",
                "Bonferroni multiplicity policy",
            ],
            excluded_history_refs=[],
            exclusion_meaning=(
                "histories incompatible with the supplied reports and fixed analysis "
                "conditions are irrelevant to this reconstruction, not nonexistent"
            ),
            correction_or_retraction_refs=[],
            interaction_rule_refs=[],
            narrowing_status="not-claimed",
            decision_effect=(
                f"types {status} as a supplied-order, baseline-relative result and "
                "blocks extrapolation to causal direction or continuous history"
            ),
        )
    return report
