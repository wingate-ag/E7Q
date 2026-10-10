# E7Q

**Auditable verification and evidence for quantum programs and experimental results.**

E7Q helps you state what must remain true, run or hand off quantum work, and
produce a reproducible Proof-of-Path showing what the evidence supports—and
what it does not.

It complements quantum SDKs rather than replacing them.

**E7Q-IR is the core architecture of E7Q:** an evidence-native quantum
intermediate representation and execution-assurance protocol connecting source
intent, transformations, execution context, observations, assessments, and
bounded claims. The native E7Q language is one supported front end into that
protocol.

## See the difference

Suppose two sets of quantum runs look similar. Did the observed distribution
remain within your declared limits, or did it materially change?

```bash
e7q drift baseline-replication.json candidate-replication.json \
  --max-total-variation 0.10 \
  --significance-level 0.05 \
  -o drift-report.json
```

E7Q validates that the campaigns are comparable, recomputes their pooled
distributions, measures total-variation distance, applies a two-sample
chi-square test, and records the result in a deterministic report.

```json
{
  "schema": "e7q.drift-report/v1",
  "status": "NO_DRIFT",
  "drift_detected": false,
  "total_variation": 0.02,
  "max_total_variation": 0.1,
  "significance_level": 0.05
}
```

`NO_DRIFT` has a deliberately narrow meaning: neither declared threshold was
breached in the supplied data. It does not authenticate the provider or
timeline, prove hardware stability, establish physical fidelity, or rule out
an undetected change.

That distinction is the point of E7Q: useful conclusions, explicit limits, and
a reviewable evidence trail.

## Why E7Q instead of just X?

| Tool | What it is primarily for | What E7Q adds |
| --- | --- | --- |
| Qiskit / Cirq | Building and executing quantum circuits | Declared invariants, verification targets, offline handoff artifacts, and bounded evidence reports |
| OpenQASM | Representing quantum programs | Higher-level intent, executable assertions, and Proof-of-Path |
| Unit tests | Checking expected software behavior | Quantum-aware equivalence criteria, evidence provenance, and explicit limits on every verdict |
| Provider dashboards | Viewing provider-specific jobs and results | Portable receipts, replication, drift, and trend reports that can be reviewed offline |
| E7G-T | General invariant-aware reasoning and projection discipline | A concrete, executable quantum-domain implementation |

Use Qiskit, Cirq, OpenQASM, and provider services for what they do well. Use E7Q
when you also need to answer:

- What was supposed to remain invariant?
- Which transformation and backend assumptions were used?
- Which evidence supports the result?
- Can another reviewer reproduce the assessment?
- What does the result not establish?

## What E7Q does

- Executes and verifies invariant-aware quantum programs.
- Compares circuits under explicit equivalence criteria.
- Supports state-vector and density-matrix reference execution.
- Represents noise channels and backend capabilities.
- Compiles against declared hardware coupling graphs with auditable SWAP-routing traces.
- Exports dependency-free Qiskit, Cirq, and OpenQASM source.
- Estimates resources and selects targets from offline calibration snapshots.
- Produces execution bundles for credentialed handoff.
- Links returned counts to execution receipts.
- Safely imports externally produced ZIP/directory evidence packages and
  verifies their manifests, counts, QASM, mappings, calibration coverage, and
  cross-file consistency without executing archive content.
- Imports the supported OpenQASM 2.0 circuit surface as a typed, non-executable
  artifact while preserving physical indices, parameters, and measurement
  destinations.
- Assesses noisy counts against deterministic bit expectations only under an
  explicit count-label order, threshold, confidence level, and claim mode.
- Assesses distributions, replication, campaign drift, longitudinal trends,
  and bounded one- or two-factor comparative experiments.
- Records temporal carrier descriptions, TD order roles, ordering, projection
  loss, phase criteria, and
  boundary crossings in machine-readable evidence.
- Validates the structure of registered E7Q artifacts.
- Offers an opt-in stabilizer-syndrome pilot with deterministic algebraic
  reports and executable reference circuits.

## What E7Q does not establish

E7Q is not a new physical theory or a replacement for established quantum
mathematics. It does not by itself:

- execute on authenticated quantum hardware;
- authenticate providers, timestamps, calibration data, or returned results;
- prove that a device is stable or physically faithful;
- establish causation from a detected statistical change;
- turn finite-sample non-detection into proof of equivalence;
- make a structurally conformant artifact semantically true.

## Five-minute start

Requires Python 3.11 or later.

```bash
git clone https://github.com/wingate-ag/E7Q.git
cd E7Q
python -m pip install -e ".[test]"

e7q verify examples/bell.e7q --proof bell.proof.json
```

### E7Q-IR v0alpha1

Build and validate a vendor-neutral evidence graph around an externally produced
circuit workflow without adopting the E7Q language:

```bash
e7q ir build examples/e7q-ir/external-circuit-workflow.json \
  -o ir-graph.json
e7q ir validate ir-graph.json --level F1 \
  -o ir-conformance.json
e7q ir inspect ir-graph.json
```

Phase 1A also accepts `--level F2` and emits deterministic per-artifact and
per-relation semantic results. Phase 1B now checks embedded QASM, counts, TVD
and claim support. Digest-only graphs block byte-dependent checks; equivalence
remains unassessed. See [Phase 1B scope](docs/e7q-ir/PHASE_1B.md).

The demonstrator hashes supplied OpenQASM files, records declared transformation
preservation and loss, validates supplied aggregate counts, performs a bounded
total-variation comparison, and links the result to an explicit claim boundary.
It does not execute the circuit or authenticate a provider. See the
[E7Q-IR architecture](docs/e7q-ir/ARCHITECTURE.md).
The authoritative implementation sequence and AI handoff instructions are in
the [E7Q-IR build plan](docs/e7q-ir/BUILD_PLAN.md).

The verifier checks every declared invariant. The generated JSON records the
initialization, transformations, measurements, probabilities, counts, and
pass/fail result.

Compare two unitary circuits under an explicit criterion:

```bash
e7q compare examples/identity-direct.e7q \
  examples/identity-optimized.e7q \
  --criterion global-phase \
  --proof equivalence.proof.json
```

Prepare an offline execution handoff and assess the returned result:

```bash
e7q bundle examples/nonlocal-cx.e7q \
  --snapshot examples/calibration-snapshot.json \
  --shots 1000 \
  -o execution-bundle.json

e7q receipt execution-bundle.json \
  --result provider-result.json \
  -o execution-receipt.json

e7q assess execution-receipt.json \
  --reference examples/bell-reference.json \
  -o execution-assessment.json
```

Inspect a supplied external execution package without authenticating or
executing it:

```bash
e7q external-bundle verify external-package.zip \
  -o external-evidence-receipt.json
```

The resulting `e7q.external-evidence-receipt/v1alpha1` keeps archive safety,
artifact integrity, internal consistency, external provenance,
reproducibility, and algorithmic claim validation separate. See the
[external evidence importer](docs/EXTERNAL_EVIDENCE_IMPORTER.md).

Import a supplied OpenQASM 2.0 circuit without allocating a simulator state:

```bash
e7q import-openqasm2 final_circuit.qasm \
  --name supplied-circuit \
  -o openqasm2-import.json
```

For an external receipt generated with `--include-counts`, run a declared
deterministic-bit assessment:

```bash
e7q assess-deterministic external-evidence-with-counts.json \
  --reference pilots/qec_syndrome/hardware_reference.json \
  -o deterministic-assessment.json
```

The reference must declare whether observed labels place classical bit zero on
the left or right. The QEC pilot profile records Qiskit's single-register
display convention as `clbit-descending` and normalizes it to E7Q's canonical
`clbit-ascending` order. See the
[OpenQASM 2 and deterministic assessment guide](docs/OPENQASM2_AND_DETERMINISTIC_ASSESSMENT.md).

### QEC syndrome-homomorphism pilot

E7Q can now make the standard stabilizer-syndrome homomorphism auditable. For
the three-qubit repetition code, this command verifies that the syndromes of
`XII`, `IXI`, and their phase-insensitive product `XXI` add modulo two:

```bash
e7q qec-homomorphism XII IXI \
  --generator ZZI \
  --generator IZZ \
  --name "three-qubit repetition code" \
  -o syndrome-homomorphism.json
```

The companion examples expose the important zero-syndrome distinction:
`III`, stabilizer `ZZI`, and logical `XXX` all produce `00`, but they are not
the same operator class. See the [QEC syndrome pilot](docs/QEC_SYNDROME_PILOT.md)
for the mathematical convention, six executable cases, independent checker,
and evidence boundary.

### Optional E7G-T UC2 observation pilot

Calibration ingestion, receipts, replication, drift, and trend commands accept
`--observation-pilot`. The flag adds a versioned experimental block that keeps
supplied records and bounded observational claims distinct from E7Q's derived
verdicts, while preserving divergence, unknowns, and temporal limits.

```bash
e7q replicate receipt-1.json receipt-2.json \
  --observation-pilot \
  -o replication-report.json
```

The module is opt-in because it remains informative in E7G-T v0.11-UC2.
Ordinary E7Q artifacts remain valid without it.

### Optional E7G-T UC3 temporal-orientation pilot

Execution bundles, receipts, replication, drift, and trend commands accept
`--temporal-orientation-pilot`. The flag adds a separate versioned block that
declares observer locality and relation kinds, and distinguishes reverse audit
or reconstruction from time-reversal symmetry and causal reversal.

```bash
e7q trend campaign-0.json campaign-1.json campaign-2.json \
  --temporal-orientation-pilot \
  -o trend-report.json
```

The profile also makes compatible-history relevance explicit without treating
excluded histories as destroyed or nonexistent. It is opt-in because the UC3
module remains informative pending Pilot H. It does not alter quantum state
evolution or identify evidential history narrowing with measurement collapse.

### E7G-T UC4 topology boundary

E7Q retains UC4's topology boundary. UC4 adds an informative mathematical
topological-overlay pilot, but ordinary E7Q routing does not invoke it. The
existing `--topology` option and `topology` artifact fields are retained for
backward compatibility and mean a hardware **coupling graph** (`linear`,
`ring`, or `all-to-all`). Graph adjacency and SWAP-routing paths are not
silently promoted to topological neighbourhoods or topological paths.

UC4 also makes Candidate Law T0 explicit: temporal extension does not itself
select temporal orientation. E7Q therefore continues to emit temporal evidence
independently of the opt-in temporal-orientation pilot.

### Optional E7G-T UC5 relative-support pilot

E7Q v1.0.0rc12 pins E7G-T v0.11-UC5. Comparative-experiment manifests may
declare an ordinal, scored, probabilistic, likelihood-like, confidence-like,
or domain-specific support model and request an embedded
`e7q.relative-support-pilot/v1alpha1` record:

```bash
e7q assess-experiment examples/comparative-experiment-synthetic.json \
  --relative-support-pilot \
  -o comparative-report.json
```

The pilot keeps candidate admissibility, support, exclusion, phase
determinacy, and action separate. Low support does not remove an alternative.
It also enforces minimum semantics-specific value domains: probabilities are
finite numbers in `[0,1]`, likelihood-like values are finite and non-negative,
and scores and confidence-like values are finite numbers. A conforming
probability value still requires a separately declared probability model.

### Comparative-experiment evidence

`assess-experiment` validates a supplied one- or two-factor manifest,
aggregates declared cells, preserves every metric, reports baseline-to-candidate
effects, and computes a descriptive interaction contrast for a complete 2x2
design. It never collapses metric trade-offs into an undeclared score.

Its claim ladder separates manifest assessability, experimental feasibility,
observed difference, repeatable effect, quality advantage, practical
advantage, and computational quantum advantage. Structural validation supports
only `MANIFEST_ASSESSABLE`; `FEASIBILITY` requires verified execution evidence.
The command can also report a descriptive `OBSERVED_DIFFERENCE` from supplied
values, while the stronger claims remain explicitly unestablished.

## Evidence and validation

E7Q's credential-free core is complete as a v1.0 release candidate.

- The parser is fail-closed for unconsumed input and ambiguous duplicate
  declarations.
- The repository test suite passes across Python 3.11–3.13.
- Independent validation compares tested behavior with NumPy, Qiskit, Cirq,
  and SciPy routes.
- Proof-of-Path artifacts are deterministic for the tested workflows.

These results support the tested software behavior within the stated
environment. They do not constitute comprehensive mathematical validation,
provider authentication, real-hardware validation, or evidence for a new
physical theory.

Artifact validation reports `PASS` with
`conformance: STRUCTURALLY_CONFORMANT` and `validation_scope: structure-only`
only when the registered schema and required top-level evidence are present.

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [Language specification](docs/E7Q_Language_Specification.md)
- [E7G-T to E7Q mapping](docs/E7GT_Quantum_Mapping.md)
- [Temporal-evidence profile](docs/TEMPORAL_EVIDENCE_PROFILE.md)
- [UC2 observational-claim pilot](docs/OBSERVATIONAL_CLAIM_PILOT.md)
- [UC3 temporal-orientation pilot](docs/TEMPORAL_ORIENTATION_PILOT.md)
- [UC5 relative-support pilot](docs/RELATIVE_SUPPORT_PILOT.md)
- [Comparative experiments](docs/COMPARATIVE_EXPERIMENTS.md)
- [rc12 release notes](docs/RELEASE_NOTES_1.0.0rc12.md)
- [QEC syndrome-homomorphism pilot](docs/QEC_SYNDROME_PILOT.md)
- [External evidence importer](docs/EXTERNAL_EVIDENCE_IMPORTER.md)
- [OpenQASM 2 and deterministic assessment](docs/OPENQASM2_AND_DETERMINISTIC_ASSESSMENT.md)
- [Roadmap](ROADMAP.md)
- [Offline completion boundary](docs/MILESTONE_18.md)
- [E7G-T upstream relationship](references/E7GT_UPSTREAM.md)

The milestone guides in [`docs/`](docs/) preserve the implementation history
and detailed usage of each capability.

## Relationship to E7G-T

E7Q is a downstream implementation of E7G-T's invariant, transformation,
projection, measurement-accountability, temporal-geometry, and Proof-of-Path
principles. E7Q v1.0.0rc12 pins E7G-T v0.11-UC5, implements a bounded temporal-
evidence profile, and offers UC2's observation/interpretation and UC3's
temporal-orientation modules plus UC5's relative-support overlay as separate
opt-in pilots for quantum workflows.
UC4's mathematical topological-overlay pilot is not implicitly activated by
E7Q's legacy coupling-graph `topology` terminology. The canonical E7G-T kernel
remains a separate upstream project and is not silently modified by E7Q.

## License

Copyright © 2026 Oleksandr Razinkov.

- Source code: [Apache License 2.0](LICENSE)
- Specifications, documentation, examples as expressive works, and
  explanatory material: [CC BY-SA 4.0](LICENSE-DOCS)

See [`NOTICE`](NOTICE) for the controlling licensing notice.

> Experimental software. Do not use E7Q as the sole basis for safety-critical,
> security-critical, financial, medical, or physical-system decisions.
