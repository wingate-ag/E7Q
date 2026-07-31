# SPDX-License-Identifier: Apache-2.0
"""Offline distribution-shift assessment between replication campaigns."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .assessment import _gamma_q
from .language import E7QError
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
    return {
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
            carrier="TD2",
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
