# SPDX-License-Identifier: Apache-2.0
"""Evidence-bounded statistical assessment of execution receipts."""
from __future__ import annotations

import json
from math import exp, isfinite, lgamma, log
from pathlib import Path
from typing import Any

from .language import E7QError


def _load(path: str | Path, schema: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise E7QError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise E7QError(f"{label} must use {schema}")
    return value


def load_receipt(path: str | Path) -> dict[str, Any]:
    return _load(path, "e7q.execution-receipt/v1", "execution receipt")


def load_reference(path: str | Path) -> dict[str, Any]:
    return _load(path, "e7q.reference-distribution/v1", "reference distribution")


def _gamma_q(a: float, x: float) -> float:
    """Regularized upper incomplete gamma, using standard series/continued fraction."""
    if a <= 0 or x < 0:
        raise E7QError("invalid chi-square parameters")
    if x == 0:
        return 1.0
    eps, tiny, limit = 1e-14, 1e-300, 1000
    if x < a + 1:
        total = term = 1.0 / a
        ap = a
        for _ in range(limit):
            ap += 1
            term *= x / ap
            total += term
            if abs(term) <= abs(total) * eps:
                break
        p = total * exp(-x + a * log(x) - lgamma(a))
        return max(0.0, min(1.0, 1.0 - p))
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, limit + 1):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) <= eps:
            break
    q = exp(-x + a * log(x) - lgamma(a)) * h
    return max(0.0, min(1.0, q))


def assess_receipt(receipt: dict[str, Any], reference: dict[str, Any]) -> dict[str, object]:
    counts = receipt.get("counts")
    shots = receipt.get("shots")
    if not isinstance(counts, dict) or not isinstance(shots, int) or shots < 1:
        raise E7QError("receipt must contain valid counts and shots")
    probabilities = reference.get("probabilities")
    if not isinstance(probabilities, dict) or len(probabilities) < 2:
        raise E7QError("reference probabilities must contain at least two outcomes")
    normalized: dict[str, float] = {}
    for outcome, probability in probabilities.items():
        if not isinstance(outcome, str) or not outcome or set(outcome) - {"0", "1"}:
            raise E7QError("reference outcomes must be binary strings")
        if not isinstance(probability, (int, float)) or isinstance(probability, bool):
            raise E7QError("reference probabilities must be numeric")
        probability = float(probability)
        if not isfinite(probability) or probability <= 0 or probability > 1:
            raise E7QError("reference probabilities must be finite and greater than zero")
        normalized[outcome] = probability
    if abs(sum(normalized.values()) - 1.0) > 1e-12:
        raise E7QError("reference probabilities must sum to one")
    if set(counts) - set(normalized):
        raise E7QError("receipt contains outcomes absent from reference")
    max_tvd = reference.get("max_total_variation", 0.1)
    alpha = reference.get("significance_level", 0.05)
    if not isinstance(max_tvd, (int, float)) or not 0 <= max_tvd <= 1:
        raise E7QError("max_total_variation must be between zero and one")
    if not isinstance(alpha, (int, float)) or not 0 < alpha < 1:
        raise E7QError("significance_level must be between zero and one")
    observed = {key: int(counts.get(key, 0)) / shots for key in normalized}
    tvd = 0.5 * sum(abs(observed[key] - normalized[key]) for key in normalized)
    expected = {key: shots * normalized[key] for key in normalized}
    chi_square = sum(
        (int(counts.get(key, 0)) - expected[key]) ** 2 / expected[key]
        for key in normalized
    )
    degrees = len(normalized) - 1
    p_value = _gamma_q(degrees / 2, chi_square / 2)
    low_expected = sorted(key for key, value in expected.items() if value < 5)
    checks = {
        "total_variation": tvd <= float(max_tvd),
        "chi_square": p_value >= float(alpha),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    proof = [
        {"step": 0, "kind": "receipt", "receipt_digest": receipt.get("result_digest"),
         "shots": shots},
        {"step": 1, "kind": "reference", "probabilities": dict(sorted(normalized.items())),
         "max_total_variation": float(max_tvd), "significance_level": float(alpha)},
        {"step": 2, "kind": "assessment", "status": status,
         "total_variation": tvd, "chi_square": chi_square, "p_value": p_value},
        {"step": 3, "kind": "evidence-boundary",
         "boundary": "Threshold consistency for supplied finite-sample evidence only; not proof of provider authenticity, device correctness, model truth, quantum advantage, or physical fidelity."},
    ]
    return {
        "schema": "e7q.execution-assessment/v1",
        "status": status,
        "shots": shots,
        "reference": dict(sorted(normalized.items())),
        "observed": dict(sorted(observed.items())),
        "total_variation": tvd,
        "max_total_variation": float(max_tvd),
        "chi_square": chi_square,
        "degrees_of_freedom": degrees,
        "p_value": p_value,
        "significance_level": float(alpha),
        "checks": checks,
        "warnings": (["chi-square approximation has expected cells below 5: " + ", ".join(low_expected)] if low_expected else []),
        "proof": proof,
    }
