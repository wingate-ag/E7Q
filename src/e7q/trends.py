# SPDX-License-Identifier: Apache-2.0
"""Offline longitudinal assessment across supplied replication campaigns."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .drift import assess_drift, load_replication_report
from .language import E7QError


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
    return {
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
        "proof": proof,
    }
