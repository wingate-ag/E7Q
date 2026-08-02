# SPDX-License-Identifier: Apache-2.0
"""Offline distribution-shift assessment between replication campaigns."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .assessment import _gamma_q
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


def load_replication_report(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise E7QError(f"invalid replication report: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != "e7q.replication-report/v1":
        raise E7QError("replication report must use e7q.replication-report/v1")
    return value


def assess_drift(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    max_total_variation: float = 0.1,
    significance_level: float = 0.05,
    include_observational_claim_pilot: bool = False,
    include_temporal_orientation_pilot: bool = False,
) -> dict[str, object]:
    """Compare pooled finite-sample distributions from two supplied campaigns."""
    if not isinstance(max_total_variation, (int, float)) or isinstance(max_total_variation, bool) or not 0 <= max_total_variation <= 1:
        raise E7QError("max_total_variation must be between zero and one")
    if not isinstance(significance_level, (int, float)) or isinstance(significance_level, bool) or not 0 < significance_level < 1:
        raise E7QError("significance_level must be between zero and one")
    target = baseline.get("target")
    if not isinstance(target, str) or not target or candidate.get("target") != target:
        raise E7QError("replication reports must identify the same target")

    rows: list[dict[str, Any]] = []
    width: int | None = None
    outcomes: set[str] = set()
    for label, report in (("baseline", baseline), ("candidate", candidate)):
        counts, shots = report.get("pooled_counts"), report.get("total_shots")
        if not isinstance(counts, dict) or not counts or not isinstance(shots, int) or isinstance(shots, bool) or shots < 1:
            raise E7QError(f"{label} report must contain pooled_counts and total_shots")
        clean: dict[str, int] = {}
        for outcome, count in counts.items():
            if not isinstance(outcome, str) or not outcome or set(outcome) - {"0", "1"}:
                raise E7QError("pooled outcomes must be binary strings")
            if width is None:
                width = len(outcome)
            if len(outcome) != width:
                raise E7QError("replication reports must use a common outcome width")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise E7QError("pooled counts must be non-negative integers")
            clean[outcome] = count
        if sum(clean.values()) != shots:
            raise E7QError(f"{label} pooled counts must sum to total_shots")
        outcomes.update(clean)
        rows.append({"label": label, "shots": shots, "counts": clean})

    ordered = sorted(outcomes)
    if len(ordered) < 2:
        raise E7QError("drift assessment requires at least two observed outcomes")
    probabilities = [
        {outcome: row["counts"].get(outcome, 0) / row["shots"] for outcome in ordered}
        for row in rows
    ]
    tvd = 0.5 * sum(abs(probabilities[0][key] - probabilities[1][key]) for key in ordered)
    combined = {key: rows[0]["counts"].get(key, 0) + rows[1]["counts"].get(key, 0) for key in ordered}
    grand = rows[0]["shots"] + rows[1]["shots"]
    active = [key for key in ordered if combined[key] > 0]
    chi_square = 0.0
    low_expected: list[str] = []
    for index, row in enumerate(rows):
        for outcome in active:
            expected = row["shots"] * combined[outcome] / grand
            if expected < 5:
                low_expected.append(f'{row["label"]}:{outcome}')
            chi_square += (row["counts"].get(outcome, 0) - expected) ** 2 / expected
    degrees = len(active) - 1
    if degrees < 1:
        raise E7QError("drift assessment requires at least two observed outcomes")
    p_value = _gamma_q(degrees / 2, chi_square / 2)
    checks = {
        "total_variation": tvd <= float(max_total_variation),
        "homogeneity": p_value >= float(significance_level),
    }
    drift_detected = not all(checks.values())
    status = "DRIFT" if drift_detected else "NO_DRIFT"
    proof = [
        {"step": 0, "kind": "campaign-linkage", "target": target, "baseline_bundle": baseline.get("bundle_digest"), "candidate_bundle": candidate.get("bundle_digest")},
        {"step": 1, "kind": "distribution-shift", "total_variation": tvd, "chi_square": chi_square, "p_value": p_value},
        {"step": 2, "kind": "drift-decision", "status": status, "checks": checks},
        {"step": 3, "kind": "evidence-boundary", "boundary": "Offline comparison of supplied pooled campaign counts only; not chronology authentication, causal attribution, provider authentication, device-stability proof, or physical-fidelity evidence."},
    ]
    report: dict[str, object] = {
        "schema": "e7q.drift-report/v1",
        "status": status,
        "drift_detected": drift_detected,
        "target": target,
        "baseline": {"bundle_digest": baseline.get("bundle_digest"), "shots": rows[0]["shots"], "probabilities": probabilities[0]},
        "candidate": {"bundle_digest": candidate.get("bundle_digest"), "shots": rows[1]["shots"], "probabilities": probabilities[1]},
        "total_variation": tvd,
        "max_total_variation": float(max_total_variation),
        "chi_square": chi_square,
        "degrees_of_freedom": degrees,
        "p_value": p_value,
        "significance_level": float(significance_level),
        "checks": checks,
        "warnings": (["chi-square homogeneity approximation has expected cells below 5: " + ", ".join(low_expected)] if low_expected else []),
        "temporal_evidence": temporal_evidence(
            temporal_order_roles=["TD2"],
            carrier_description="declared baseline-candidate campaign pair",
            order_relation="declared baseline before candidate",
            chronology_status="declared-not-authenticated",
            projection_from="two pooled replication campaigns",
            projection_to="distribution-shift assessment",
            preserves=[
                "declared baseline-candidate roles",
                "pooled distributions",
                "threshold decision",
            ],
            loses=[
                "authenticated elapsed time",
                "intermediate device trajectory",
                "causal explanation",
            ],
            reconstruction_status="non-unique",
            reconstruction_limit=(
                "The observed shift metrics are compatible with multiple "
                "intermediate histories and causes."
            ),
            criterion_id="e7q.drift-threshold",
            criterion_edition="1",
            criterion_parameters={
                "max_total_variation": float(max_total_variation),
                "significance_level": float(significance_level),
            },
            criterion=(
                f"total variation <= {float(max_total_variation)} and "
                f"homogeneity p-value >= {float(significance_level)}"
            ),
            phase=status,
            boundary_crossing={
                "detected": drift_detected,
                **(
                    {"reason": "declared drift threshold breach"}
                    if drift_detected
                    else {}
                ),
            },
        ),
        "proof": proof,
    }
    if include_observational_claim_pilot:
        observation_records: list[dict[str, object]] = []
        observational_claims: list[dict[str, object]] = []
        for index, (label, source) in enumerate(
            (("baseline", baseline), ("candidate", candidate))
        ):
            record_id = f"observation:{label}-replication-report"
            claim_id = f"claim:{label}-pooled-counts"
            source_ref = str(source.get("bundle_digest") or f"{label}:{index}")
            observer_ref = f"software-process:e7q:{label}-report:{source_ref}"
            limitations = [
                "the supplied replication report is itself a derived artifact",
                "chronology, provider identity, and independence are not authenticated",
            ]
            unknowns = [
                "intermediate campaign and device history",
                "causes of any distributional difference",
            ]
            observation_records.append(
                observation_record(
                    observation_id=record_id,
                    observer_ref=observer_ref,
                    modelled_entity_ref=source_ref,
                    inquiry_profile_ref="e7q.drift-threshold",
                    semantic_context_ref="e7q.replication-report/v1",
                    viewing_or_measurement_ref="supplied pooled campaign counts",
                    observation_protocol_ref="e7q.drift-input/v1",
                    observed_at_or_during={"declared_role": label},
                    temporal_support={
                        "role": label,
                        "order_status": "declared-not-authenticated",
                    },
                    spatial_or_population_support={
                        "target": target,
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
            observational_claims.append(
                observational_claim(
                    claim_id=claim_id,
                    observation_record_refs=[record_id],
                    asserted_content=(
                        f"The supplied {label} replication report contains the "
                        "recorded pooled counts and shot total."
                    ),
                    evidence_path=[source_ref, "drift input validation"],
                    temporal_support={"declared_role": label, "authenticated": False},
                    resolution="one pooled campaign distribution",
                    known_limitations=limitations,
                    unknown_positions=unknowns,
                    blocked_overread=[
                        "the report establishes a complete or authenticated device history"
                    ],
                )
            )
        report["observational_claim_pilot"] = observational_claim_pilot(
            pilot_id="e7q.drift-report",
            observation_records=observation_records,
            observational_claims=observational_claims,
            interpretations=[
                interpretation_record(
                    interpretation_id="interpretation:drift-status",
                    supporting_observation_claim_refs=[
                        "claim:baseline-pooled-counts",
                        "claim:candidate-pooled-counts",
                    ],
                    assumption_refs=[
                        "baseline and candidate roles reflect the intended comparison"
                    ],
                    inference_rule_refs=["chi-square homogeneity approximation"],
                    bridge_refs=["pooled counts to empirical distributions"],
                    external_model_refs=["multinomial finite-sample model"],
                    criterion_refs=["e7q.drift-threshold@1"],
                    conclusion=f"{status} under the declared drift thresholds.",
                    inherited_limitations=[
                        "input reports do not authenticate chronology or causal independence"
                    ],
                    added_limitations=(
                        ["some expected chi-square cells are below five"]
                        if low_expected
                        else []
                    ),
                    support_basis="mixed",
                    support_status="operationally-validated-offline",
                    admissible_use="compare the two supplied pooled distributions",
                    non_admissible_use=(
                        "causal attribution, continuous monitoring, future stability, "
                        "or provider and device authentication"
                    ),
                    validity_window="the declared baseline-candidate pair",
                    stop_or_reopen_condition=(
                        "reopen if either report, threshold, role, or provenance changes"
                    ),
                )
            ],
            shared_field=shared_observational_field(
                participating_observer_refs=[
                    "software-process:e7q:baseline-report:"
                    + str(baseline.get("bundle_digest") or "baseline:0"),
                    "software-process:e7q:candidate-report:"
                    + str(candidate.get("bundle_digest") or "candidate:1"),
                ],
                participating_observation_record_refs=[
                    "observation:baseline-replication-report",
                    "observation:candidate-replication-report",
                ],
                jointly_admissible_claim_refs=[
                    "claim:baseline-pooled-counts",
                    "claim:candidate-pooled-counts",
                ],
                divergences=[
                    {
                        "total_variation": tvd,
                        "chi_square": chi_square,
                        "p_value": p_value,
                    }
                ],
                unknowns=[
                    "causal explanation for the observed difference",
                    "unobserved intervals between campaigns",
                ],
                semantic_conditions=["common target and outcome width"],
                temporal_conditions=["declared baseline-before-candidate role only"],
                resolution_conditions=["pooled campaign distributions"],
                provenance_conditions=["supplied replication-report artifacts"],
                admissibility_conditions=["valid pooled counts and shot totals"],
                independence_conditions=["campaign independence is not established"],
            ),
        )
    if include_temporal_orientation_pilot:
        report["temporal_orientation_pilot"] = temporal_orientation_pilot(
            pilot_id="e7q.drift-report",
            orientation_ref="declared baseline-to-candidate comparison",
            observer_temporal_locality_ref="offline review after both campaign reports",
            directional_relation_kinds=[
                "sequence",
                "observationalPrecedence",
                "reconstructivePrecedence",
                "dependency",
                "globalConsistency",
            ],
            reverse_representation_ref="candidate-to-baseline descriptive traversal",
            preserved_under_reversal=[
                "campaign membership",
                "pooled distributions",
                "symmetric distance value",
            ],
            reversed_hidden_or_unsupported=[
                "declared baseline/candidate roles",
                "authenticated chronology",
                "causal explanation",
            ],
            time_reversal_symmetry_status="not-assessed",
            causal_reversal_status="unsupported",
            final_constraint_refs=["e7q.drift-threshold@1"],
            global_consistency_refs=["common target and outcome width"],
            history_whole_ref="declared baseline-candidate campaign pair",
            clock_or_synchronisation_model_ref=(
                "declared role order only; elapsed time is not authenticated"
            ),
            accumulated_valid_record_ref="validated baseline and candidate reports",
            compatible_history_family_ref="temporal_evidence.reconstruction",
            fixed_condition_refs=[
                str(baseline.get("bundle_digest") or "baseline"),
                str(candidate.get("bundle_digest") or "candidate"),
                "e7q.drift-threshold@1",
            ],
            excluded_history_refs=[],
            exclusion_meaning=(
                "histories incompatible with the supplied pooled reports do not "
                "support this reconstruction; no ontological conclusion follows"
            ),
            correction_or_retraction_refs=[],
            interaction_rule_refs=[],
            narrowing_status="not-claimed",
            decision_effect=(
                f"types {status} as a baseline-relative statistical interpretation, "
                "not a causal direction or a reversed physical process"
            ),
        )
    return report
