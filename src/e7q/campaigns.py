# SPDX-License-Identifier: Apache-2.0
"""Offline repeatability assessment across linked execution receipts."""
from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path
from typing import Any, Iterable

from .assessment import _gamma_q
from .language import E7QError


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
        normalized.append({"index": index, "shots": shots, "counts": clean, "result_digest": digest})

    ordered = sorted(outcomes)
    if len(ordered) < 2:
        raise E7QError("replication requires at least two observed outcomes")
    total_shots = sum(run["shots"] for run in normalized)
    pooled_counts = {outcome: sum(run["counts"].get(outcome, 0) for run in normalized) for outcome in ordered}
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
    return {
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
        "proof": proof,
    }
