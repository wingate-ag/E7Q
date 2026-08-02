# E7Q observational-claim pilot

E7Q v1.0rc3 implements E7G-T v0.11-UC2's observational-claim module as an
explicitly opt-in experiment. The module is informative upstream and remains
experimental in E7Q. Ordinary artifacts remain valid when this block is absent.

## Why the pilot exists

Quantum-workflow artifacts often place supplied data and derived verdicts next
to each other. That can make a provider-reported count table look as though it
directly establishes `PASS`, `DRIFT`, device stability, or physical fidelity.
The pilot separates four different things:

1. the observer-indexed record produced under a declared viewing or protocol;
2. the bounded claim licensed by that record;
3. the interpretation produced through declared assumptions, rules, bridges,
   models, and criteria;
4. any decision or reliance that follows from the interpretation.

The dependency arrows do not imply automatic entailment. Each step may add
selection, loss, assumptions, uncertainty, or a decision threshold.

## Invocation

Use `--observation-pilot` with supported offline commands:

```bash
e7q ingest-calibration vendor-export.json \
  --provider ibm \
  --max-age-hours 24 \
  --observation-pilot \
  -o calibration.json

e7q receipt execution-bundle.json \
  --result provider-result.json \
  --observation-pilot \
  -o execution-receipt.json

e7q replicate receipt-1.json receipt-2.json \
  --observation-pilot \
  -o replication-report.json

e7q drift baseline.json candidate.json \
  --observation-pilot \
  -o drift-report.json

e7q trend campaign-1.json campaign-2.json campaign-3.json \
  --observation-pilot \
  -o trend-report.json
```

The equivalent Python APIs accept
`include_observational_claim_pilot=True`.

## Record shape

The optional top-level member is:

```json
{
  "observational_claim_pilot": {
    "schema": "e7q.observational-claim-pilot/v1alpha1",
    "upstream_module": "E7G-T v0.11-UC2 sections 3.9, 16.6, and 19.7",
    "status": "informative-pilot",
    "invoked": true,
    "pilot_id": "e7q.replication-report",
    "observation_records": [],
    "observational_claims": [],
    "interpretations": [],
    "shared_field": {
      "participating_observer_refs": [],
      "participating_observation_record_refs": [],
      "jointly_admissible_claim_refs": [],
      "divergences": [],
      "unknowns": [],
      "composition_conditions": {
        "semantic": [],
        "temporal": [],
        "resolution": [],
        "provenance": [],
        "admissibility": [],
        "independence": []
      }
    },
    "temporal_extension_bridges": []
  }
}
```

Single-record workflows may use `null` for `shared_field`. An empty
`temporal_extension_bridges` list means that no extension beyond the recorded
temporal support is licensed.

## Current workflow classification

| Workflow content | Pilot classification |
|---|---|
| Supplied vendor calibration export | Observation record |
| Supplied provider result and aggregate counts | Observation record |
| Statement that the supplied artifact reports those values | Observational claim |
| Freshness status under a maximum-age rule | Interpretation |
| Receipt `PASS` under linkage and count rules | Interpretation |
| Replication `PASS` or `FAIL` under statistical thresholds | Interpretation |
| `DRIFT` or `NO_DRIFT` | Interpretation |
| `TREND_DETECTED` or `NO_TREND_DETECTED` | Interpretation |
| Pairwise or campaign differences | Shared-field divergence |
| Run independence, device history, missing intervals | Shared-field unknowns |

## Validation

`e7q validate-artifact` checks the optional pilot when it is present. The
validator checks required record context, non-empty claim support, unique IDs,
record-to-claim and claim-to-interpretation reference integrity, use
boundaries, shared-field references, and composition-condition lists.

This is structural validation. It does not authenticate providers, recompute
all statistics, prove independence, certify hardware, or establish physical
fidelity.

## Pilot G evaluation

E7Q is one scientific/software-measurement case for E7G-T Pilot G. Each pilot
case should compare:

```text
ordinary review
vs UC1 source/view + support + reconstruction analysis
vs the UC2 observational-claim module
```

Record whether the UC2 module uniquely or more clearly exposes an over-broad
claim, hidden interpretation, undeclared criterion, erased divergence,
assumed independence, unsupported temporal extension, changed next move, or
unacceptable record burden. E7Q's implementation does not itself validate or
promote UC2's candidate laws.

## Boundary

The pilot does not define `Reality(observer)`. An admissible observation field
limits what may support the current inquiry; it is not a complete ontology.
Agreement among records is not automatically truth or independence. Absence of
a recorded event is not proof that no event occurred outside the declared
system, boundary, resolution, or validity window.
