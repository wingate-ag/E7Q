# E7Q Temporal-Evidence Profile

E7Q v1.0rc3 implements a bounded operational profile of the E7G-T v0.11-UC2
temporal subkernel. The profile makes temporal claims in offline quantum
workflows explicit and reviewable without altering quantum execution
semantics.

## Record

Generated artifacts may contain:

```json
{
  "temporal_evidence": {
    "schema": "e7q.temporal-evidence/v2",
    "temporal_order_roles": ["TD2"],
    "carrier_description": "ordered family of supplied campaign histories",
    "order_relation": "user-supplied sequence with baseline-relative comparisons",
    "chronology_status": "declared-not-authenticated",
    "projection": {
      "from": "ordered replication-report family",
      "to": "baseline-relative longitudinal trend report",
      "preserves": [
        "supplied order",
        "campaign identity",
        "first declared threshold breach"
      ],
      "loses": [
        "authenticated chronology and elapsed time",
        "unobserved intermediate campaigns",
        "causal explanation"
      ]
    },
    "reconstruction": {
      "status": "non-unique",
      "limit": "The series does not determine unobserved intervals or a unique causal history."
    },
    "temporal_phase": {
      "criterion_id": "e7q.trend-threshold",
      "criterion_edition": "1",
      "parameters": {
        "max_total_variation": 0.1,
        "family_significance_level": 0.05,
        "adjusted_significance_level": 0.025,
        "multiplicity_method": "bonferroni"
      },
      "description": "declared statistical thresholds",
      "status": "TREND_DETECTED"
    },
    "boundary_crossing": {
      "detected": true,
      "first_index": 2
    }
  }
}
```

## Operational meanings

| Field | Meaning |
| --- | --- |
| `temporal_order_roles` | E7G-T TD0--TD7 order roles supported by the artifact |
| `carrier_ref` | Optional reference to the concrete source artifact or history family |
| `carrier_description` | Human-readable description of that concrete carrier |
| `order_relation` | Actual sequence or family relation represented |
| `chronology_status` | Strength of the evidence for chronological claims |
| `clock` | Timestamp field and its evidence status, if applicable |
| `validity_window` | Declared freshness policy and evaluated result |
| `projection` | Richer temporal source reduced to the current view |
| `reconstruction` | Whether and within what limits the richer source can be recovered |
| `temporal_phase` | Status under an identified, editioned criterion and explicit parameters |
| `boundary_crossing` | Whether and where the criterion was crossed |

TD0--TD7 are order roles, not temporal carriers. A receipt or campaign history
is the carrier; `TD0`, `TD1`, or `TD2` describes the temporal order role the
carrier supports in the current inquiry.

## Compatibility

New artifacts use `e7q.temporal-evidence/v2`. Structural validation continues
to accept existing `e7q.temporal-evidence/v1` records, where the legacy
`carrier` field contains one TD role. New code should use
`temporal_order_roles` and, when available, `carrier_ref`.

## Chronology statuses

- `not-applicable`: temporal order does not apply to the artifact;
- `not-established`: the artifact supplies a family without an order;
- `proof-order-only`: only logical Proof-of-Path order is established;
- `declared-not-authenticated`: order was supplied but not authenticated;
- `format-validated-not-authenticated`: timestamp syntax and timezone were
  validated, but provenance was not authenticated;
- `provider-reported-not-authenticated`: a supplied provider result reports the
  time, but E7Q did not authenticate it;
- `authenticated`: reserved for an external integration that supplies
  verifiable authentication evidence.

## Projection discipline

An aggregate result does not uniquely determine its execution history. Counts,
pooled distributions, drift metrics, and trend reports are projections that
preserve declared evidence while hiding shot order, intermediate states,
unobserved intervals, and possible causal structure.

## Boundary

This profile is not a new quantum theory of time. TD0–TD7 are modelling roles,
not literal physical time dimensions. The profile does not establish
many-worlds branching, provider-authenticated chronology, continuous
monitoring, causation, hardware stability, or physical fidelity.
