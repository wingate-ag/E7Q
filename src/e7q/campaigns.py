# SPDX-License-Identifier: Apache-2.0
"""Offline repeatability assessment across linked execution receipts."""
from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path
from typing import Any, Iterable

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


def load_replication_receipts(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in paths:
        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise E7QError(f"invalid execution receipt: {exc}") from exc
        if not isinstance(value, dict) or value.get("schema") != "e7q.execution-receipt/v1":
            raise E7QError("execution receipt must use e7q.execution-receipt/v1")
        receipts.append(value)
    if len(receipts) < 2:
        raise E7QError("replication requires at least two execution receipts")
    return receipts


def assess_replication(
    receipts: list[dict[str, Any]],
    *,
    max_pairwise_tvd: float = 0.1,
    significance_level: float = 0.05,
    include_observational_claim_pilot: bool = False,
    include_temporal_orientation_pilot: bool = False,
) -> dict[str, object]:
    """Assess distributional consistency across independently supplied receipts."""
    if len(receipts) < 2:
        raise E7QError("replication requires at least two execution receipts")
    if not isinstance(max_pairwise_tvd, (int, float)) or isinstance(max_pairwise_tvd, bool) or not 0 <= max_pairwise_tvd <= 1:
        raise E7QError("max_pairwise_tvd must be between zero and one")
    if not isinstance(significance_level, (int, float)) or isinstance(significance_level, bool) or not 0 < significance_level < 1:
        raise E7QError("significance_level must be between zero and one")

    bundle = receipts[0].get("bundle_digest")
    target = receipts[0].get("target")
    if not isinstance(bundle, str) or not bundle or not isinstance(target, str) or not target:
        raise E7QError("receipts must identify bundle_digest and target")
    digests: set[str] = set()
    normalized: list[dict[str, Any]] = []
    outcomes: set[str] = set()
    width: int | None = None
    for index, receipt in enumerate(receipts):
        if receipt.get("bundle_digest") != bundle or receipt.get("target") != target:
            raise E7QError("all receipts must link to the same bundle and target")
        digest = receipt.get("result_digest")
        if not isinstance(digest, str) or not digest or digest in digests:
            raise E7QError("receipts must have unique result_digest values")
        digests.add(digest)
        shots, counts = receipt.get("shots"), receipt.get("counts")
        if not isinstance(shots, int) or isinstance(shots, bool) or shots < 1 or not isinstance(counts, dict) or not counts:
            raise E7QError("each receipt must contain valid shots and counts")
        clean: dict[str, int] = {}
        for outcome, count in counts.items():
            if not isinstance(outcome, str) or not outcome or set(outcome) - {"0", "1"}:
                raise E7QError("receipt outcomes must be binary strings")
            if width is None:
                width = len(outcome)
            if len(outcome) != width:
                raise E7QError("receipt outcomes must have equal width")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise E7QError("receipt counts must be non-negative integers")
            clean[outcome] = count
        if sum(clean.values()) != shots:
            raise E7QError("receipt counts must sum to shots")
        outcomes.update(clean)
        normalized.append({
            "index": index,
            "shots": shots,
            "counts": clean,
            "result_digest": digest,
            "provider": receipt.get("provider", "unknown"),
            "completed_at": receipt.get("completed_at"),
        })

    total_shots = sum(run["shots"] for run in normalized)
    pooled_counts = {
        outcome: sum(run["counts"].get(outcome, 0) for run in normalized)
        for outcome in sorted(outcomes)
    }
    ordered = [outcome for outcome, count in pooled_counts.items() if count > 0]
    pooled_counts = {outcome: pooled_counts[outcome] for outcome in ordered}
    if len(ordered) < 2:
        raise E7QError("replication requires at least two observed outcomes")
    pooled = {outcome: pooled_counts[outcome] / total_shots for outcome in ordered}
    run_probabilities = [
        {outcome: run["counts"].get(outcome, 0) / run["shots"] for outcome in ordered}
        for run in normalized
    ]
    pairwise = []
    for left, right in combinations(range(len(normalized)), 2):
        tvd = 0.5 * sum(abs(run_probabilities[left][key] - run_probabilities[right][key]) for key in ordered)
        pairwise.append({"left": left, "right": right, "total_variation": tvd})
    maximum_tvd = max(item["total_variation"] for item in pairwise)

    chi_square = 0.0
    low_expected: list[str] = []
    for index, run in enumerate(normalized):
        for outcome in ordered:
            expected = run["shots"] * pooled[outcome]
            if expected == 0:
                continue
            if expected < 5:
                low_expected.append(f"run {index}:{outcome}")
            chi_square += (run["counts"].get(outcome, 0) - expected) ** 2 / expected
    degrees = (len(normalized) - 1) * (len(ordered) - 1)
    p_value = _gamma_q(degrees / 2, chi_square / 2)
    checks = {
        "pairwise_total_variation": maximum_tvd <= float(max_pairwise_tvd),
        "homogeneity": p_value >= float(significance_level),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    proof = [
        {"step": 0, "kind": "campaign-linkage", "bundle_digest": bundle, "target": target, "runs": len(normalized)},
        {"step": 1, "kind": "pooled-evidence", "total_shots": total_shots, "probabilities": pooled},
        {"step": 2, "kind": "repeatability-assessment", "status": status, "maximum_pairwise_tvd": maximum_tvd, "chi_square": chi_square, "p_value": p_value},
        {"step": 3, "kind": "evidence-boundary", "boundary": "Offline consistency of user-supplied linked receipts only; not provider authentication, independence proof, device correctness, reference truth, quantum advantage, or physical fidelity."},
    ]
    report: dict[str, object] = {
        "schema": "e7q.replication-report/v1",
        "status": status,
        "bundle_digest": bundle,
        "target": target,
        "runs": len(normalized),
        "total_shots": total_shots,
        "pooled_counts": pooled_counts,
        "pooled_probabilities": pooled,
        "run_probabilities": run_probabilities,
        "pairwise": pairwise,
        "maximum_pairwise_tvd": maximum_tvd,
        "max_pairwise_tvd": float(max_pairwise_tvd),
        "chi_square": chi_square,
        "degrees_of_freedom": degrees,
        "p_value": p_value,
        "significance_level": float(significance_level),
        "checks": checks,
        "warnings": (["chi-square homogeneity approximation has expected cells below 5: " + ", ".join(low_expected)] if low_expected else []),
        "temporal_evidence": temporal_evidence(
            temporal_order_roles=["TD2"],
            carrier_ref=bundle,
            carrier_description="family of supplied execution runs",
            order_relation="unordered replication family",
            chronology_status="not-established",
            projection_from="linked execution receipts",
            projection_to="pooled replication report",
            preserves=[
                "per-run identity",
                "pairwise distribution distances",
                "pooled counts",
            ],
            loses=[
                "run chronology",
                "inter-run device history",
                "shot-level temporal structure",
            ],
            reconstruction_status="non-unique",
            reconstruction_limit=(
                "The pooled report does not determine a unique run chronology "
                "or device trajectory."
            ),
            criterion_id="e7q.replication-consistency",
            criterion_edition="1",
            criterion_parameters={
                "max_pairwise_tvd": float(max_pairwise_tvd),
                "significance_level": float(significance_level),
            },
            criterion=(
                f"maximum pairwise TVD <= {float(max_pairwise_tvd)} and "
                f"homogeneity p-value >= {float(significance_level)}"
            ),
            phase=status,
            boundary_crossing={
                "detected": status == "FAIL",
                **(
                    {"reason": "repeatability threshold breach"}
                    if status == "FAIL"
                    else {}
                ),
            },
        ),
        "proof": proof,
    }
    if include_observational_claim_pilot:
        records: list[dict[str, object]] = []
        claims: list[dict[str, object]] = []
        record_refs: list[str] = []
        claim_refs: list[str] = []
        observer_refs: list[str] = []
        for run in normalized:
            index = run["index"]
            record_id = f"observation:execution-receipt:{index}"
            claim_id = f"claim:reported-run-counts:{index}"
            observer_ref = (
                f"reported-observing-system:{run['provider']}:"
                f"{run['result_digest']}"
            )
            limitations = [
                "provider identity, chronology, and execution were not authenticated",
                "aggregate counts omit shot order and intermediate states",
            ]
            unknowns = [
                "causal device history",
                "independence from the other supplied runs",
                "unrecorded events between runs",
            ]
            records.append(
                observation_record(
                    observation_id=record_id,
                    observer_ref=observer_ref,
                    modelled_entity_ref=str(run["result_digest"]),
                    inquiry_profile_ref="e7q.replication-consistency",
                    semantic_context_ref="e7q.execution-receipt/v1",
                    viewing_or_measurement_ref="normalized aggregate outcome counts",
                    observation_protocol_ref="e7q.replication-input/v1",
                    observed_at_or_during=run["completed_at"],
                    temporal_support={
                        "reported_completion": run["completed_at"],
                        "order_status": "not-established",
                    },
                    spatial_or_population_support={
                        "target": target,
                        "shots": run["shots"],
                    },
                    resolution="one aggregate count distribution per supplied run",
                    recorded_content={
                        "shots": run["shots"],
                        "counts": dict(sorted(run["counts"].items())),
                    },
                    provenance_refs=[str(run["result_digest"])],
                    evidence_refs=[bundle, str(run["result_digest"])],
                    known_limitations=limitations,
                    unknown_positions=unknowns,
                )
            )
            claims.append(
                observational_claim(
                    claim_id=claim_id,
                    observation_record_refs=[record_id],
                    asserted_content=(
                        f"Supplied receipt {index} records {run['shots']} shots "
                        "with the declared aggregate counts."
                    ),
                    evidence_path=[
                        str(run["result_digest"]),
                        "receipt count validation",
                        "replication input normalization",
                    ],
                    temporal_support={
                        "reported_completion": run["completed_at"],
                        "authenticated": False,
                    },
                    resolution="one aggregate count distribution",
                    known_limitations=limitations,
                    unknown_positions=unknowns,
                    blocked_overread=[
                        "the run was independent of every other supplied run",
                        "the provider or device history was authenticated",
                    ],
                )
            )
            record_refs.append(record_id)
            claim_refs.append(claim_id)
            if observer_ref not in observer_refs:
                observer_refs.append(observer_ref)
        report["observational_claim_pilot"] = observational_claim_pilot(
            pilot_id="e7q.replication-report",
            observation_records=records,
            observational_claims=claims,
            interpretations=[
                interpretation_record(
                    interpretation_id="interpretation:replication-status",
                    supporting_observation_claim_refs=claim_refs,
                    assumption_refs=[
                        "all supplied receipts represent the same bundle and target"
                    ],
                    inference_rule_refs=["chi-square homogeneity approximation"],
                    bridge_refs=["finite counts to empirical distributions"],
                    external_model_refs=["multinomial finite-sample model"],
                    criterion_refs=["e7q.replication-consistency@1"],
                    conclusion=f"{status} under the declared repeatability thresholds.",
                    inherited_limitations=[
                        "run provenance, chronology, and independence are not authenticated"
                    ],
                    added_limitations=(
                        ["some expected chi-square cells are below five"]
                        if low_expected
                        else []
                    ),
                    support_basis="mixed",
                    support_status="operationally-validated-offline",
                    admissible_use="compare supplied finite-sample run distributions",
                    non_admissible_use=(
                        "proof of run independence, device stability, provider identity, "
                        "physical fidelity, or future performance"
                    ),
                    validity_window="the supplied receipt family only",
                    stop_or_reopen_condition=(
                        "reopen if receipts, thresholds, provenance, or independence "
                        "evidence changes"
                    ),
                )
            ],
            shared_field=shared_observational_field(
                participating_observer_refs=observer_refs,
                participating_observation_record_refs=record_refs,
                jointly_admissible_claim_refs=claim_refs,
                divergences=pairwise,
                unknowns=[
                    "causal dependence among runs",
                    "unobserved device history between runs",
                    "authenticated run chronology",
                ],
                semantic_conditions=["common target and bundle digest"],
                temporal_conditions=["replication family is treated as unordered"],
                resolution_conditions=["aggregate count distributions only"],
                provenance_conditions=["unique supplied result digests"],
                admissibility_conditions=["valid counts summing to declared shots"],
                independence_conditions=[
                    "independence is not established by distinct result digests"
                ],
            ),
        )
    if include_temporal_orientation_pilot:
        report["temporal_orientation_pilot"] = temporal_orientation_pilot(
            pilot_id="e7q.replication-report",
            orientation_ref="unordered family comparison from completed receipt set",
            observer_temporal_locality_ref="offline review after all supplied receipts",
            directional_relation_kinds=["dependency", "globalConsistency"],
            reverse_representation_ref=None,
            preserved_under_reversal=[],
            reversed_hidden_or_unsupported=[
                "run chronology",
                "inter-run causal direction",
            ],
            time_reversal_symmetry_status="not-assessed",
            causal_reversal_status="unsupported",
            final_constraint_refs=["replication consistency thresholds"],
            global_consistency_refs=["common bundle digest and target"],
            history_whole_ref="supplied execution-receipt family",
            clock_or_synchronisation_model_ref="none; replication family is unordered",
            accumulated_valid_record_ref="validated supplied receipt family",
            compatible_history_family_ref="temporal_evidence.reconstruction",
            fixed_condition_refs=[
                bundle,
                target,
                "e7q.replication-consistency@1",
            ],
            excluded_history_refs=[],
            exclusion_meaning=(
                "no run chronology is excluded or selected by the unordered "
                "replication assessment"
            ),
            correction_or_retraction_refs=[],
            interaction_rule_refs=[],
            narrowing_status="not-claimed",
            decision_effect=(
                "prevents receipt list order from being treated as chronology and "
                "prevents consistency or divergence from becoming a causal claim"
            ),
        )
    return report
