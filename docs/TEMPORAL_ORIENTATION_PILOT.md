# E7Q temporal-orientation pilot

E7Q v1.0rc5 implements E7G-T v0.11-UC3's temporal-orientation,
observer-locality, and history-relevance module as an opt-in profile. The
module is informative pending E7G-T Pilot H and does not alter E7Q's quantum
execution semantics.

## Invocation

Use `--temporal-orientation-pilot` with execution-bundle, receipt,
replication, drift, or trend workflows. The corresponding Python APIs accept
`include_temporal_orientation_pilot=True`.

```bash
e7q trend campaign-0.json campaign-1.json campaign-2.json \
  --temporal-orientation-pilot \
  -o trend-report.json
```

Ordinary artifacts remain valid when the pilot is absent. If the
`temporal_orientation_pilot` block is present, `e7q validate-artifact` checks
its structure and anti-conflation boundaries.

## Record boundary

The schema is `e7q.temporal-orientation-pilot/v1alpha1`. It records:

- the declared temporal orientation and observer temporal locality;
- typed directional relations;
- any reverse representation and what it preserves, reverses, hides, or does
  not support;
- separate time-reversal-symmetry and causal-reversal statuses;
- final constraints and global-consistency references;
- a history-whole, clock model, accumulated record, compatible-history
  family, and fixed conditions;
- excluded histories, the strictly epistemic meaning of exclusion,
  corrections or retractions, and interaction rules;
- whether narrowing is claimed and what responsible decision the pilot
  changes.

The relation vocabulary is deliberately typed:

```text
clockPrecedence
sequence
dependency
observationalPrecedence
reconstructivePrecedence
generativeCausation
finalConstraint
globalConsistency
```

These relations may coincide under a declared model but are never silently
identified.

## Quantum boundary

Compatible-history relevance narrowing is an evidential reconstruction rule.
It is not E7Q's computational-basis measurement update, a many-worlds claim,
or ontological collapse. Reversing a Proof-of-Path or report traversal does
not show that a quantum process ran backwards, that its dynamics are
time-reversal symmetric, or that later results caused earlier operations.

The pilot does not establish retrocausation, fundamental time neutrality,
supertime, physical realisation of alternative histories, provider
chronology, or a unique physical device history.

## E7G-T Pilot H use

The E7Q pilot cases compare ordinary temporal reporting, the existing UC2
temporal/observational profile, and this UC3 record. Promotion would require
evidence that the additional fields prevent material orientation, causation,
simultaneity, or relevance-collapse conflations without imposing unacceptable
burden. E7Q therefore exposes the fields experimentally and does not make them
part of ordinary artifact conformance.
