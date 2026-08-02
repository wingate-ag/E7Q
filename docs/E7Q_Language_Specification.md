# E7Q Language Specification

**Version:** 1.0.0-rc5
**Status:** experimental draft
**Documentation licence:** CC-BY-SA-4.0

## 1. Purpose

E7Q describes quantum computations with intended invariants, equivalence
criteria, measurement context, and an auditable execution path. Standard
quantum mathematics is normative for execution. E7G-T supplies the
modelling and accountability vocabulary.

## 2. Program model

A program contains exactly one context, exactly one quantum register, exactly
one classical register, zero or more distinct invariant kinds, one or more
uniquely named paths, and exactly one verification target. Context-setting
keys are unique within the context block. Duplicate singleton declarations,
context keys, invariant kinds, or path names are invalid; an implementation
must reject them rather than select or overwrite one silently. A path is an
ordered sequence of unitary transformations, measurements, classically
conditioned transformations, assertions, and reusable-path references.

## 3. Core types and context

- `qubits q[n]`: an n-qubit register initially in `|0…0⟩`;
- `bits c[n]`: an n-bit classical register initially containing zeroes;
- context settings: `backend`, `shots`, and optional deterministic `seed`.
  No other context-setting keys are permitted. `shots` must be a positive
  integer, and `seed`, when present, must be a non-negative integer. The
  reference backends are `statevector` and `densitymatrix`.

## 4. Operations

The gates `X`, `Y`, `Z`, `H`, `S`, `T`, `CX`, `CZ`, and `SWAP` have their
conventional matrix semantics.

`measure q -> c` measures the complete quantum register into the classical
register and must terminate the path. `measure q[i] -> c[j]` measures and
collapses one qubit, stores the result, and permits subsequent operations.

`if c[j] == b G q[i]` applies the one-qubit gate `G` only when classical bit
`c[j]` equals `b`, where `b` is zero or one.

`use PathName` expands another declared path at the point of use. References
must exist and must not be recursive.

`assert c[j] == b` checks the classical value for every shot. It contributes a
verification check and records its failed-shot count and Proof-of-Path step.

`noise bit_flip(p) q[i]`, `noise phase_flip(p) q[i]`, and
`noise depolarizing(p) q[i]` apply declared single-qubit quantum channels with
`0 <= p <= 1`. Noise currently requires the `densitymatrix` backend and
terminal full-register measurement.

## 5. Invariants

`normalized` requires the final per-shot state norm to be one within numerical
tolerance. `outcomes in {…}` constrains classical-register-width bitstrings.
For dynamic execution, the constraint applies to all observed shot outcomes.

## 6. Execution

Purely unitary paths followed by full-register measurement retain exact ideal
probabilities. Dynamic paths execute shot by shot: each measurement samples
the Born distribution, collapses and renormalizes the state, records its
classical result, and controls later conditional gates.

The density-matrix backend evolves `ρ` by `UρU†` and noise by Kraus maps. It
reports trace and purity after every transformation or channel. This reference
model does not claim fidelity to an unspecified physical device.

## 7. Equivalence profiles

The implemented profiles are exact unitary equality, equality up to global
phase, computational-basis measurement equivalence, and tolerance equality.
Programs containing partial measurement or classical control are not
unitaries and must be rejected by these profiles. Compatible density-matrix
programs additionally support exact and tolerance-based superoperator
equality and computational-basis measurement-behaviour equality. Channel
comparison excludes mid-circuit measurement, classical control, and
assertions.

## 8. Proof-of-Path

A report records initialization, ordered transformations, projections,
classical conditions, assertions, executed and skipped branch counts, final
outcomes, and invariant results. When an assertion fails, `first_failure`
identifies its step and failed-shot count. This is evidence for the declared
execution, not proof of a new physical theory.

For noisy execution, the report distinguishes `transform`, `channel`, and
`project` steps and records channel probability, trace, and purity. A backend
capability profile declares required features and preserves the boundary
between reference simulation and hardware-specific compilation.

Topology compilation accepts an explicit undirected coupling graph and native
gate set. A non-adjacent two-qubit operation is routed along a shortest path by
inserting a forward SWAP chain, applying the operation, and reversing the
chain. Restoring the logical layout preserves later measurement and classical
control semantics. The compilation report records the physical path, inserted
SWAP count, capability assumptions, and boundary between compilation evidence
and physical execution.

Vendor adapters translate supported static E7Q programs into dependency-free
Python source for IBM Qiskit or Google Cirq. They accept the core gate set and
terminal full-register measurement. Noise, assertions, partial measurement,
and classical control are rejected explicitly. Adapter evidence identifies the
target and operation count, and does not imply SDK installation, job submission,
device calibration, execution, or fidelity.

## 9. Conformance

A v0.5 implementation must retain Bell and equivalence behaviour, execute the
reference teleportation and Deutsch–Jozsa programs, export their supported
operations to OpenQASM 3, compose non-recursive paths, diagnose failed
assertions, round-trip the supported OpenQASM subset, reject invalid
references, and reject dynamic programs from unitary comparison.
It must additionally preserve density-matrix trace under all supported
channels, expose noise-aware evidence and capability requirements, and reject
noise on the state-vector backend.
Topology conformance requires rejection of disconnected coupling graphs and
unsupported native gates, semantics preservation after routing, and an
auditable compilation trace. It does not imply hardware fidelity.
Vendor-adapter conformance requires syntactically valid Python output, complete
static gate and measurement coverage, Proof-of-Path evidence, and explicit
rejection of unsupported program features.


## 10. Resource planning

Resource planning schedules quantum operations into dependency-safe layers,
reports logical and routed gate counts, total depth, two-qubit depth, and SWAP
overhead, and preserves the compilation trace. These values are static
properties of the reference program and selected topology. They do not predict
queue time, monetary cost, device calibration, execution success, or fidelity.

Planning conformance requires deterministic estimates, serialization of gates
sharing a qubit, parallel eligibility for disjoint gates, terminal-measurement
barriers, and a machine-readable boundary statement.

## 11. Calibration snapshots and target selection

A calibration snapshot is a user-supplied, timestamped document declaring
target availability, qubit capacity, topology, native gates, queue depth, and
aggregate single-qubit, two-qubit, and readout error rates. E7Q validates the
snapshot, rejects incompatible targets, topology-compiles each viable target,
and ranks candidates using a documented success proxy.

Selection evidence must distinguish supplied observations from calculated
estimates and include rejected-target reasons. A selection is advisory: it
does not establish live calibration, vendor authenticity, execution cost,
queue time at submission, or physical fidelity.


## 12. Offline vendor calibration ingestion

E7Q may normalize user-supplied IBM/Qiskit-style and Google/Cirq-style
calibration exports into `e7q.calibration/v1`. An adapter must validate its
provider-specific schema, an ISO 8601 timestamp with timezone, target fields,
probability ranges, and an optional maximum-age policy. It must retain provider
and source-schema provenance in the normalized snapshot.

Ingestion is an offline transformation of supplied evidence. Conformance does
not imply network access, vendor authentication, authenticity verification,
live calibration retrieval, job submission, cost knowledge, or guaranteed
hardware fidelity.


## 13. Reproducible execution bundles

E7Q may combine a source program and a supplied calibration snapshot into an
`e7q.execution-bundle/v1` artifact. The bundle must identify its inputs with
SHA-256 digests, name the selected target, contain the topology-routed OpenQASM,
record the shot count and resource plan, and include Proof-of-Path evidence.

Bundle creation is deterministic for identical inputs. A conforming bundle must
distinguish `READY` from `submitted` and default to `submitted: false`.
It is an offline handoff artifact: it does not establish vendor authentication,
job acceptance, queue state, price, physical fidelity, or measured results.


## 14. Execution-result receipts

E7Q may normalize a user-supplied `e7q.execution-result/v1` document against
an `e7q.execution-bundle/v1` artifact. It must validate target and shot
linkage, require non-negative integer counts whose total equals the declared
shots, and record empirical probabilities, input digests, provider metadata,
and Proof-of-Path evidence in `e7q.execution-receipt/v1`.

Receipt conformance establishes internal consistency of the supplied files
only. It does not authenticate the provider, prove that E7Q submitted or
witnessed the job, establish live calibration, or claim cost or physical
fidelity.


## 15. Statistical result assessment

E7Q may assess an `e7q.execution-receipt/v1` against a supplied
`e7q.reference-distribution/v1`. The reference must assign non-negative
probabilities summing to one and declare a maximum total-variation distance
and significance level. The assessment reports total-variation distance,
Pearson's chi-square statistic, degrees of freedom, and an asymptotic p-value.

A PASS means only that the supplied empirical distribution satisfies both
declared thresholds for this finite sample. It does not prove the reference
model, provider authenticity, device correctness, quantum advantage, or
physical fidelity. Small expected cell counts weaken the chi-square
approximation and must be disclosed in the report.

## 16. Replication campaigns

E7Q may assess two or more `e7q.execution-receipt/v1` artifacts that identify
the same execution bundle and target. Each receipt must have a unique result
digest, valid counts, and a common outcome width. The resulting
`e7q.replication-report/v1` pools counts, records every pairwise
total-variation distance, and applies a Pearson chi-square homogeneity test.

A PASS means only that the supplied runs satisfy both declared repeatability
thresholds. It does not prove run independence, provider authenticity, device
correctness, reference truth, quantum advantage, or physical fidelity. Small
expected cells weaken the asymptotic homogeneity test and must be disclosed.


## 17. Campaign drift assessment

E7Q may compare two `e7q.replication-report/v1` artifacts for a common
target. Each report must contain valid pooled counts, total shots, binary
outcomes of a common width, and at least two outcomes across the comparison.
The resulting `e7q.drift-report/v1` records pooled probabilities,
total-variation distance, a two-sample Pearson chi-square homogeneity test,
explicit thresholds, warnings, and Proof-of-Path evidence.

`NO_DRIFT` means only that both supplied finite-sample distributions satisfy
the declared thresholds. `DRIFT` means at least one threshold fails. Neither
status authenticates collection time or provider, identifies a cause, proves
device stability, or establishes physical fidelity. Low expected cells weaken
the asymptotic test and must be disclosed.

## 18. Longitudinal trend assessment

E7Q may compare an ordered series of three or more
`e7q.replication-report/v1` artifacts against the first supplied report as a
declared baseline. Reports must identify a common target and compatible binary
outcome space. The resulting `e7q.trend-report/v1` records each
baseline-relative total-variation distance and chi-square result, applies a
Bonferroni-adjusted significance level across repeated comparisons, and
identifies the first threshold breach.

`NO_TREND_DETECTED` means only that no supplied candidate breached either
declared threshold. `TREND_DETECTED` means at least one did. File order is a
user declaration, not authenticated chronology. Neither verdict proves
continuous monitoring, provider authenticity, causation, device stability, or
physical fidelity.

## 19. Bounded temporal-evidence profile

E7Q implements a bounded quantum-workflow profile of the E7G-T v0.11-UC3
temporal subkernel. Time is treated as an admitted structure that may be
extended, ordered, projected, summarized, phase-classified, and checked for
declared boundary crossings. This profile governs evidence semantics only;
established quantum mathematics remains normative for execution.

The machine-readable subrecord uses schema `e7q.temporal-evidence/v2` and
contains:

- `temporal_order_roles`: one or more E7G-T roles such as `TD0`, `TD1`, or
  `TD2`;
- `carrier_ref`, when available: a stable reference to the concrete artifact or
  history family;
- `carrier_description`: a human-readable description of that concrete
  carrier;
- `order_relation`: the actual ordering supported by the artifact;
- `chronology_status`: whether chronology is absent, declared, format-validated,
  provider-reported, proof-order-only, or authenticated;
- `clock`, when applicable: the timestamp field, value, and evidential status;
- `validity_window`, when evaluated: the declared freshness criterion and
  result;
- `projection`: richer temporal source, derived view, preserved structure, and
  hidden or lost structure;
- `reconstruction`: whether the richer temporal source is reconstructible from
  the view and the declared limit of that reconstruction;
- `temporal_phase`: criterion identifier, edition, parameters, description,
  and resulting inquiry-relative status;
- `boundary_crossing`: whether the declared criterion was crossed and, where
  available, the first supplied index or reason.

The bounded order-role mapping is:

| Order role | E7Q interpretation |
| --- | --- |
| `TD0` | one calibration snapshot, measurement, receipt, or reported event |
| `TD1` | one ordered execution, compilation, Proof-of-Path, or handoff history |
| `TD2` | a branch family, replication family, campaign comparison, or longitudinal history family |
| `TD3`–`TD7` | reserved for future use cases that provide operational definitions and evidence |

Newly generated calibration, execution-bundle, execution-receipt, replication,
drift, and trend artifacts include the subrecord. Existing v1 artifacts without
it remain readable. Structural validation also continues to accept legacy
`e7q.temporal-evidence/v1` subrecords, where `carrier` contained one TD role.
If `temporal_evidence` is present, structural conformance must validate its
schema, order roles, declared order, chronology status,
projection, reconstruction, and any supplied clock, phase, or
boundary-crossing fields. A claim of authenticated chronology must include an
authentication evidence reference.

Temporal phase means equivalence under a declared operational criterion. It
does not mean a physical phase of matter. `NO_DRIFT` and
`NO_TREND_DETECTED` are inquiry-relative statuses over supplied finite data,
not proofs of temporal stability. File order, Proof-of-Path order,
provider-reported timestamps, authenticated chronology, elapsed duration, and
causal order are distinct and must not be silently substituted for one
another.

This profile does not claim literal additional time dimensions, many-worlds
branching, a new quantum theory of time, authenticated provider chronology,
continuous observation, or reconstruction of a unique execution history from
aggregate counts.

## 20. Optional observational-claim pilot

E7Q implements the informative E7G-T v0.11-UC2 observational-claim module as
the opt-in schema `e7q.observational-claim-pilot/v1alpha1`. It is not part of
ordinary E7Q artifact conformance and is never emitted unless explicitly
requested.

The pilot maintains the support dependency:

```text
declared viewing and protocol
  -> observation record
  -> observational claim
  -> interpretation
```

An observation record identifies the observer or observing system, modelled
entity, inquiry, semantic context, viewing or measurement, protocol, temporal
and population support, resolution, recorded content, provenance, evidence,
limitations, and unknown positions. An observational claim states only what
one or more such records license. An interpretation exposes its assumptions,
rules, bridges, external models, criteria, inherited and added limitations,
admissible use, blocked use, validity window, and reopen condition.

Where several records are composed, `shared_field` preserves:

- `jointly_admissible_claim_refs`;
- `divergences`;
- `unknowns`;
- semantic, temporal, resolution, provenance, admissibility, and independence
  conditions.

The currently piloted workflows are calibration ingestion, execution receipts,
replication reports, drift reports, and trend reports. Their `PASS`, `FAIL`,
`DRIFT`, `NO_DRIFT`, `TREND_DETECTED`, and `NO_TREND_DETECTED` statuses are
interpretations under declared criteria, not direct observations.

The CLI flag `--observation-pilot` invokes the module for those workflows.
Structural artifact validation checks internal record and claim references when
the optional block is present. The pilot does not establish provider identity,
run independence, authenticated chronology, physical fidelity, causation,
future stability, consensus as truth, or an observer-relative ontology.

## 21. Optional temporal-orientation pilot

E7Q implements the informative E7G-T v0.11-UC3 temporal-orientation module as
the separate opt-in schema `e7q.temporal-orientation-pilot/v1alpha1`. It is not
emitted unless requested and is not required for ordinary artifact
conformance.

The pilot declares temporal orientation, observer temporal locality, and one
or more typed directional relations. It records any reverse representation,
the structure preserved or unsupported under reversal, and separate statuses
for time-reversal symmetry and causal reversal. It also names the relevant
history-whole, clock model, accumulated record, compatible-history family,
fixed conditions, excluded histories, corrections, retractions, and
interaction rules.

The CLI flag `--temporal-orientation-pilot` invokes the profile for execution
bundles, receipts, replication, drift, and trend workflows. Structural
artifact validation checks the optional block when present.

Reverse Proof-of-Path traversal or later-to-earlier reconstruction does not
establish dynamically admissible reverse execution or backward physical
causation. Joint history-whole membership does not establish clock
simultaneity. Compatible-history relevance narrowing is an epistemic limit on
the current reconstruction under fixed conditions; it is distinct from E7Q's
computational-basis measurement update and does not establish ontological
collapse, retrocausation, fundamental time neutrality, supertime, or physical
realisation of alternative histories.

## 22. Offline artifact conformance

E7Q registers the stable offline artifact families produced by calibration
ingestion, execution handoff, result normalization, statistical assessment,
replication, drift, and trend analysis. A conforming implementation may emit
an `e7q.conformance-report/v1` that checks a declared artifact schema and its
required top-level evidence.

A conformance `PASS`, additionally labelled `STRUCTURALLY_CONFORMANT`,
establishes structural compatibility only. It does not
recompute every semantic claim, authenticate a provider, attest chronology or
run independence, prove hardware execution, or establish physical fidelity.
The v1.0 release boundary is the credential-free, provider-neutral toolchain;
live vendor integrations remain optional external adapters.
